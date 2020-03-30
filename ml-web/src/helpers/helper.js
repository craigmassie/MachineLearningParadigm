export function createJsonPayload(modelLocation, datasetLocation, epochs) {
	const payload = new Object();
	payload.model_location = modelLocation;
	payload.dataset_location = datasetLocation;
	payload.epochs = epochs;
	return payload;
}
