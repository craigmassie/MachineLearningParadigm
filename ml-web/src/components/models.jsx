import React, { Component } from 'react';
import Model from './model';
import Popover, { ArrowContainer } from 'react-tiny-popover';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faInfoCircle } from '@fortawesome/free-solid-svg-icons';

class Models extends Component {
	state = {
		isPopoverOpen: false
	};

	render() {
		if (this.props.models) {
			console.log(this.props.models);
			const availableModels = this.props.models.map((m, index) => (
				<Model key={index} modelName={m} trainFunc={this.props.trainFunc} modelDescription="hello1" />
			));
			return (
				<React.Fragment>
					<div className="archName">
						<h1 id="inlineHeader">{this.props.architecture}</h1>
						<Popover
							isOpen={this.state.isPopoverOpen}
							position={'right'} // preferred position
							content={({ position, targetRect, popoverRect }) => (
								<ArrowContainer // if you'd like an arrow, you can import the ArrowContainer!
									position={position}
									targetRect={targetRect}
									popoverRect={popoverRect}
									arrowColor={'rgb(228, 228, 228)'}
									arrowSize={10}
									arrowStyle={{ opacity: 0.7 }}
								>
									<div className="popOverText">{this.props.architectureInfo}</div>
								</ArrowContainer>
							)}
						>
							<span
								id="faInfo"
								onClick={() => this.setState({ isPopoverOpen: !this.state.isPopoverOpen })}
							>
								<FontAwesomeIcon icon={faInfoCircle} />
							</span>
						</Popover>
					</div>
					<div className="cards-list">{availableModels}</div>
				</React.Fragment>
			);
		}
	}
}

export default Models;
