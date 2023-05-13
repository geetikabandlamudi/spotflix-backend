import { DynamoDBClient, PutItemCommand } from "@aws-sdk/client-dynamodb";

const client = new DynamoDBClient({ region: "us-east-1" });

export const saveToDynamoDB = async (videoFileName, thumbnailName) => {
  const params = {
    TableName: "thumbnail",
    Item: {
      "videoName": { S: videoFileName },
      "thumbnailName": { S: thumbnailName }
    }
  };

  try {
    const command = new PutItemCommand(params);
    const response = await client.send(command);
    console.log("Data saved to DynamoDB:", response);
  } catch (err) {
    console.error("Error saving data to DynamoDB:", err);
  }
};