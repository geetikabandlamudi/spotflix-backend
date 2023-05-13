import fs from "fs";
import path from "path";
import doesFileExist from "./does-file-exist.mjs";
import downloadVideoToTmpDirectory from "./download-video-to-tmp-directory.mjs";
import generateThumbnailsFromVideo from "./generate-thumbnails-from-video.mjs";
import generatePreview from "./generate-preview.mjs";
import { saveToDynamoDB } from "./save-to-dynamodb.mjs";
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

const THUMBNAILS_TO_CREATE = 1;
const PREVIEW_DURATION = 10;
const wipeTmpDirectory = async () => {
    const files = await fs.promises.readdir("/tmp/");
    const filePaths = files.map(file => path.join("/tmp/", file));
    await Promise.all(filePaths.map(file => fs.promises.unlink(file)));
};

export const extractParams = event => {
	const videoFileName = decodeURIComponent(event.Records[0].s3.object.key).replace(/\+/g, " ");
	const triggerBucketName = event.Records[0].s3.bucket.name;
	return { videoFileName, triggerBucketName };
};

export const pushToSQS = async (event) => {
	
	const sqsClient = new SQSClient({ region: "us-east-1" });
	const videoFileName = decodeURIComponent(event.Records[0].s3.object.key).replace(/\+/g, " ");
	let response;
	var params = {
	  DelaySeconds: 10,
	  MessageAttributes: {"video-name": {DataType: "String", StringValue: videoFileName}},
	  MessageBody: "New video uploaded",
	  QueueUrl: "https://sqs.us-east-1.amazonaws.com/615778613671/uploaded-video"
	};
	
	try {
    	const data = await sqsClient.send(new SendMessageCommand(params));
	    if (data) {
	      console.log("Success, message sent. MessageID:", data.MessageId);
	      const bodyMessage = 'Message Send to SQS- Here is MessageId: ' +data.MessageId;
	      response = {
	        statusCode: 200,
	        body: JSON.stringify(bodyMessage),
	      };
	    }else{
	      response = {
	        statusCode: 500,
	        body: JSON.stringify('Some error occured !!')
	      };
	    }
	    return response;
	  }
	  catch (err) {
	    console.log("Error", err);
	  }
};


export const handler = async (event) => {
    console.log("Hello, world!");
    pushToSQS(event);
    await wipeTmpDirectory();
	const { videoFileName, triggerBucketName } = extractParams(event);
	console.log(`${videoFileName} was uploaded to ${triggerBucketName}`);
	const tmpVideoPath = await downloadVideoToTmpDirectory(triggerBucketName, videoFileName);
    console.log(`Video downloaded to ${tmpVideoPath}`);
	if (doesFileExist(tmpVideoPath)) {
		const thumbnailName = await generateThumbnailsFromVideo(tmpVideoPath, THUMBNAILS_TO_CREATE, videoFileName);
		//await saveToDynamoDB(videoFileName, thumbnailName);
		
		const previewName = await generatePreview(tmpVideoPath, PREVIEW_DURATION, videoFileName);
		console.log("preview name" + previewName);
		console.log(previewName);
	}
	
    console.log("Done!");
    return {'video-name': videoFileName}
};

