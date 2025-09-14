import { getTopTaxiAreas } from "../utils/mapapi.utils.js";

/**
 * Get taxi availability - controller
 *
 * @param {*} req
 * @param {*} res
 * @param {*} next
 */
export const getTaxiAvailability = async (req, res, next) => {
    
    try {
        const topkres = await getTopTaxiAreas();
        res.status(200).json({ success: true, data: topkres });
    } catch (err) {
        console.log("error in getTaxiAvailability controller", err.message);
        next(err);
    }
};