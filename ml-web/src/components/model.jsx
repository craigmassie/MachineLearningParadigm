import React, { Component } from 'react';
import { fileNameExtract, getParentDirectory } from '../helpers/helper';

class Model extends Component {
	state = {};

	render() {
		return (
			<div
				className="card"
				onClick={() => this.props.trainFunc(this.props.modelName, this.props.modelDescription)}
			>
				<div className="card_image">
					<img src="https://i.redd.it/b3esnz5ra34y.jpg" />
				</div>
				<div className="card_title title-white">
					<p>
						{this.props.parentName ? (
							getParentDirectory(this.props.modelName)
						) : (
							fileNameExtract(this.props.modelName)
						)}
					</p>
				</div>
			</div>
		);
	}
}

export default Model;
