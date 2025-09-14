import { Router } from "express";

import { upload } from "../middleware/multer.middleware.js"
import {
    cancelTranslation,
    getLastJob,
    getTranslationProgress,
    translateBook,
    translateBookFile,
} from "../controllers/translation.controller.js";

const router = Router();

router.get("/last_job", getLastJob);
router.get("/translation_progress", getTranslationProgress);
router.post("/translate_book", translateBook);
router.post("/translate_book/file_upload", upload.single("file"), translateBookFile);
router.post("/cancel_translation", cancelTranslation);

export default router;