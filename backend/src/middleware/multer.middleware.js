import multer from "multer";
export const upload = multer({
    limits: { fileSize: 10 * 1024 * 1024 }  // 10mb
});  // memory storage, not saved to disk (only proxying to FastAPI)