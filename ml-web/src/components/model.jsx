import React, { Component } from 'react';
import { fileNameExtract } from '../helpers/helper';

class Model extends Component {
	state = {};

	render() {
		console.log('This model: ' + this.props.modelName);
		return (
			<div
				className="card"
				onClick={() => this.props.trainFunc(this.props.modelName, this.props.modelDescription)}
			>
				<div className="card_image">
					{' '}
					<img
						src="https://upload.wikimedia.org/wikipedia/commons/d/d3/Cloud-Machine-Learning-Engine-Logo.svg"
						class="filter-green"
					/>{' '}
				</div>
				<div className="card_title title-white">
					<p>{fileNameExtract(this.props.modelName)}</p>
				</div>
			</div>
		);
	}
}

export default Model;
