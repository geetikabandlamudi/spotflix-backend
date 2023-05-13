import fs from "fs";
import { S3 } from "@aws-sdk/client-s3";
import { spawnSync } from "child_process";
import doesFileExist from "./does-file-exist.mjs";
import generateTmpFilePath from "./generate-tmp-file-path.mjs";


const ffprobePath = "/opt/bin/ffprobe";
const ffmpegPath = "/opt/bin/ffmpeg";

const PREVIEW_TARGET_BUCKET = "<preview-bucket>";

export default async (tmpVideoPath, duration, videoFileName) => {
    const tmpPreviewPath = await createPreviewFromVideo(tmpVideoPath, duration, videoFileName);
    console.log("created tmpPreviewPath " + tmpPreviewPath);
    const previewName = [];
    if (doesFileExist(tmpPreviewPath)) {
        const previewNameToCreate = generateNameOfPreviewToUpload(videoFileName);
        await uploadPreviewToS3(tmpPreviewPath, previewNameToCreate);
        previewName.push(previewNameToCreate);
        console.log(" preview name added " + previewNameToCreate);
        
    }
    return previewName[0];
};

const getVideoDuration = (tmpVideoPath) => {
    const ffprobe = spawnSync(ffprobePath, [
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nk=1",
        tmpVideoPath
    ]);

    //console.log("fprobe obj" + ffprobe);
    //console.log("duration " + ffprobe.stdout.toString());
    //return Math.floor(ffprobe.stdout.toString());
};

const createPreviewFromVideo = (tmpVideoPath, duration, videoFileName) => {
    const tmpPreviewPath = generatePreviewPath(videoFileName);
    
    const ffmpegParams = createFfmpegParamsForPreview(tmpVideoPath, tmpPreviewPath, duration);
    //getVideoDuration(tmpVideoPath);
    const res = spawnSync(ffmpegPath, ffmpegParams);
    console.log(res.stdout.toString());
    console.log(spawnSync(ffmpegPath, ["-i", tmpVideoPath]).stdout.toString());
    
    //console.log("spawnSync res " + Node.Child_process.readAs(res));
//     ffmpeg()
//         .input(inputPath)
//   .inputOptions([`-ss ${startTimeInSeconds}`])
//   .outputOptions([`-t ${fragmentDurationInSeconds}`])
//   .noAudio()
//   .output(outputPath)
//   .on('end', resolve)
//   .on('error', reject)
//   .run();

    return tmpPreviewPath;
};

const generatePreviewPath = (videoFileName) => {
    //const tmpPreviewPathTemplate = "/tmp/preview-"+videoFileName+".mp4";
    const tmpPreviewPathTemplate = "/tmp/preview--{HASH}.gif";
    const uniquePreviewPath = generateTmpFilePath(tmpPreviewPathTemplate);
    return uniquePreviewPath;
};


const createFfmpegParamsForPreview = (tmpVideoPath, tmpPreviewPath, duration) => {
    console.log("temp video path" + tmpVideoPath + " tmp preview path" + tmpPreviewPath);
    // return [
    //      "-i ", tmpVideoPath,
    //     "-ss ", 5,
    //      "-t ", duration,
    //     tmpPreviewPath
        
    // ];
    return [
        "-ss", 10,
        "-i", tmpVideoPath,
        "-to", duration,
        "-an",
        tmpPreviewPath
    ];
};

const generateNameOfPreviewToUpload = (videoFileName) => {
    const strippedExtension = videoFileName.replace(".mp4", "");
    return `${strippedExtension}.gif`;
};

const uploadPreviewToS3 = async (tmpPreviewPath, nameOfPreviewToCreate) => {
    const contents = fs.createReadStream(tmpPreviewPath);
    const uploadParams = {
        Bucket: PREVIEW_TARGET_BUCKET,
        Key: nameOfPreviewToCreate,
        Body: contents,
        ContentType: "image/gif"
    };

    const s3 = new S3();
    await s3.putObject(uploadParams);
};


