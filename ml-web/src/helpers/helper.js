export function createJsonPayload(modelLocation, datasetLocation, epochs, autoType = '', trials = 0) {
	const payload = new Object();
	payload.model_location = modelLocation;
	payload.dataset_location = datasetLocation;
	payload.epochs = epochs;
	if (autoType.length > 0) {
		payload.auto_type = autoType;
	}
	if (trials > 0) {
		payload.trials = trials;
	}
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

export function getParentDirectory(filename) {
	const splitFilename = filename.replace(/\/$/, '').split('/');
	return splitFilename[splitFilename.length - 2];
}

export async function blobToString(blob) {
	const fileReader = new FileReader();
	return new Promise((resolve, reject) => {
		fileReader.onloadend = (ev) => {
			resolve(ev.target.result);
		};
		fileReader.onerror = reject;
		fileReader.readAsText(blob);
	});
}
