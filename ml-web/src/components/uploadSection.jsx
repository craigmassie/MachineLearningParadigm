import React, { Component } from 'react';
import Dropzone from 'react-dropzone';
import { BounceLoader } from 'react-spinners';

class UserUploader extends Component {
	state = {
		uploaderVisibility: true,
		uploadedDatatype: ''
	};

	determineAvailableModels(fileExtension) {
		let imageTypes = [ 'jpg', 'png', 'bmp', 'gif' ];
		if (imageTypes.indexOf(fileExtension) >= 0) {
			return 'image';
		} else {
			return 'whatever else';
		}
	}

	fileExtensionExtract(filename) {
		return filename.split('.').pop();
	}

	handleDrop(acceptedFiles) {
		let fileExtension = '';
		console.log(acceptedFiles);
		acceptedFiles.forEach((file) => {
			if (fileExtension == '') {
				fileExtension = this.fileExtensionExtract(file.name);
			} else if (this.fileExtensionExtract(file.name) !== fileExtension) {
				console.log('Inconsistent data types passed to web app.');
			}
			const reader = new FileReader();
			reader.onabort = () => console.log('file reading was aborted');
			reader.onerror = () => console.log('file reading has failed');
			reader.onload = () => {
				const binaryStr = reader.result;
				console.log(binaryStr);
			};
			reader.readAsArrayBuffer(file);
		});
		this.setState({ uploadedDatatype: this.determineAvailableModels(fileExtension) });
    }
    
    searchingHandler(){
        this.props.nowSearching();
        this.setState({uploaderVisibility: !this.state.uploaderVisibility});
    }

	render() {
		return (
			<div>
				{this.state.uploaderVisibility ? (
					<div className="uploadSection">
						<Dropzone onDrop={(acceptedFiles) => this.handleDrop(acceptedFiles)}>
							{({ getRootProps, getInputProps }) => (
								<section>
									<div {...getRootProps()}>
										<input {...getInputProps()} />
										<p>Drag 'n' drop some files here, or click to select files</p>
									</div>
								</section>
							)}
						</Dropzone>)
					</div>
				) : (
					<div>
						<BounceLoader />
						<p id="searchPlaceholder">Searching for models of type: {this.state.uploadedDatatype}</p>
					</div>
				)}
                 			<button id="fabNext" onClick={() => this.searchingHandler()}>Next</button>
			</div>
		);
	}
}

export default UserUploader;
