import {ADD_FILES} from '../actions/actions'
import { combineReducers } from 'redux'

const initialState = {
    files: []
}

function files(state=[], action){
    switch(action.type){
        case ADD_FILES:
            return action.files
        default:
            return state
    }
}

const fileManagement = combineReducers({
        files
    })

export default fileManagement;