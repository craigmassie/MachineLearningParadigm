# MLWeb APIs
MLWeb was designed with a component-based architecture in mind, with 3 Docker containers acting as the distributed backend of the system, and an independent React.js service acting as the web application. These docker containers are Flask applications, written in Python, split into the tasks of: model training, model prediction, and model explanation.

This repository contains the source code for the APIs, but the accompanying front-end source code can be found at [craigmassie/mlweb-front](https://github.com/craigmassie/mlweb-front). Both repositories were designed for a proof-of-concept evaluation as part of a MSci dissertation, and as such, may be a bit ugly in parts. Bear with me.
