import axios from "axios";

import { FAST_API_URL, forward } from "../utils/fastapi.utils.js";

/**
  * Translate a book given its text, target language, and optional email for notifications.
  *
  * @param {*} req
  * @param {*} res
  * @param {*} next
  */
 const translateBook = (req, res, next) => {
    
    try {
        forward(res, axios.post(`${FAST_API_URL}/translate_book`, req.body));
    } catch (error) {
        console.log("error in translateBook controller", error.message);
        next(error);
    }
};

/**
 * Translate a book by uploading a file, specifying the target language and optional email for notifications.
 *
 * @param {*} req
 * @param {*} res
 * @param {*} next
 */
const translateBookFile = async (req, res, next) => {
    
    try {
        const bookText = req.file.buffer.toString("utf-8");
        const { language, email } = req.body;
        const response = await axios.post(`${FAST_API_URL}/translate_book`, {
            book: bookText,
            language,
            email
        });

        res.status(200).json(response.data);
    } catch (error) {
        console.log("error in translateBookFile controller", error.message);
        next(error);
    }
};

/**
 * Get the progress of an ongoing translation job using its job ID.
 *
 * @param {*} req
 * @param {*} res
 * @param {*} next
 */
const getTranslationProgress = (req, res, next) => {
    
    try {
        forward(res, axios.get(`${FAST_API_URL}/translation_progress`, {
            params: req.query
        }));
    } catch (error) {
        console.log("error in getTranslationProgress controller", error.message);
        next(error);
    }
};

/**
 * Cancel an ongoing translation job using its job ID.
 *
 * @param {*} req
 * @param {*} res
 * @param {*} next
 */
const cancelTranslation = (req, res, next) => {
    
    try {
        forward(res, axios.post(`${FAST_API_URL}/cancel_translation`, req.body));
    } catch (error) {
        console.log("error in cancelTranslation controller", error.message);
        next(error);
    }
};

/**
 * Retrieve details of the most recent translation job.
 *
 * @param {*} req
 * @param {*} res
 * @param {*} next
 */
const getLastJob = async (req, res, next) => {
    
    try {
        forward(res, axios.get(`${FAST_API_URL}/last_job`, {
            params: req.query
        }));
    } catch (error) {
        console.log("error in getLastJob controller", error.message);
        next(error);
    }
};