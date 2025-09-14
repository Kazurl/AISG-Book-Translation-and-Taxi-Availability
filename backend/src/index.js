import bodyParser from "body-parser";
import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import path from "path";

import taxiAvailabilityRoutes from "./routes/taxiAvailability.route.js";
import translationRoutes from "./routes/translation.route.js";
import { fileURLToPath } from "url";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5001;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename)

// middleware  // todo: middleware
app.use(cors({
    origin: "http://localhost:3000",
    credentials: true,  // allows cookies/ auth headers to be sent with req
}));
app.use(express.json({ limit: "10mb" }));  // to parse req.body
app.use(express.urlencoded({ limit: "10mb", extended: true }));


// routes
app.use("/api/translation", translationRoutes);
app.use("/api/taxi-availability", taxiAvailabilityRoutes);


// If in production phase, then make the dist folder in frontend into static assets
// This allows the frontend to be joined with the backend under the same domain
// Meaning client and server both under same domain
if (process.env.NODE_ENV === "production") {
    // serve static files from React app
    app.use(express.static(path.join(__dirname, "../../frontend/dist/index.html")));

    // If any routes aside from:
    // "/api/translation" and "/api/taxi-availability" visited, then go to react application via index.html
    app.get("*splat", (req, res) => {
        res.sendFile(path.join(__dirname, "../../frontend/dist/index.html"));
    });
}


app.use((err, req, res, next) => {  // error handler middleware
    res.status(500).json({ success: false, message: process.env.NODE_ENV === "production" ? "Internal Server Error" : err.message });
})

// start server
app.listen(PORT, () => {
    console.log("Server is running on port " + PORT)
});