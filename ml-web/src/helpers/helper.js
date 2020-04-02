export function createJsonPayload(modelLocation, datasetLocation, epochs) {
	const payload = new Object();
	payload.model_location = modelLocation;
	payload.dataset_location = datasetLocation;
	payload.epochs = epochs;
	return payload;
}

export function fileExtensionExtract(filename) {
	return filename.split('.').pop();
}

export function fileNameExtract(fileLocation) {
	return fileLocation.replace(/^.*[\\\/]/, '').split('.')[0];
}

export function fileCurrentDirectory(filename) {
	return filename.substring(0, Math.max(filename.lastIndexOf('/'), filename.lastIndexOf('\\')));
}

// // A helper function used to read a Node.js readable stream into a string
// export
