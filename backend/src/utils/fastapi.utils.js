import axios from "axios";
import dotenv from "dotenv";

dotenv.config();

const FAST_API_PORT = process.env.FAST_API_PORT || 8000;
export const FAST_API_URL = `http://localhost:${FAST_API_PORT}`;


/**
 * Forward axios promise result to express response
 *
 * @export
 * @param {*} res
 * @param {*} axiosPromise
 */
export function forward(res, axiosPromise) {
    
    axiosPromise
        .then(apiRes => res.status(200).json(apiRes.data))
        .catch(err => {
            if (err.response) {
                res.status(err.response.status).json(err.response.data);
            }
            else {
                res.status(500).json({ error: err.message });
            }
        });
};