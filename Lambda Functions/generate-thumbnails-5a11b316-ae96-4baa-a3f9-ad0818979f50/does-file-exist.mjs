import fs from "fs";

export default (filePath) => {
	console.log(fs.existsSync(filePath));
	if (fs.existsSync(filePath)) {
		const stats = fs.statSync(filePath);
		const fileSizeInBytes = stats.size;

		if (fileSizeInBytes > 0) {
            console.log(`${filePath} exists!`); // Remove this once your proof-of-concept is working
			return true;
		} else {
			console.error(`${filePath} exists but is 0 bytes in size`);
			return false;
		}
	} else {
		console.error(`${filePath} does not exist`);
		return false;
	}
};