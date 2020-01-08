/*
 * action types
 */
export const ADD_FILES = 'ADD_FILES'

/*
 * action creators
 */
export function addFiles(files) {
  return { type: ADD_FILES, files }
}