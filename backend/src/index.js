import bodyParser from "body-parser";
import cors from "cors";
import dotenv from "dotenv";
import express from "express";

import translationRoutes from "./routes/translation.route.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5001;

// middleware  // todo: middleware
app.use(cors({
    origin: "http://localhost:3000",
    credentials: true,  // allows cookies/ auth headers to be sent with req
}));
app.use(express.json({ limit: "10mb" }));  // to parse req.body
app.use(express.urlencoded({ limit: "10mb", extended: true }));


// routes
app.use("/api/translation", translationRoutes);


app.use((err, req, res, next) => {  // error handler middleware
    res.status(500).json({ success: false, message: process.env.NODE_ENV === "production" ? "Internal Server Error" : err.message });
})

// start server
app.listen(PORT, () => {
    console.log("Server is running on port " + PORT)
});