import express from "express";
import bodyParser from "body-parser";
import env from "dotenv";
import path from "path";
import axios from "axios";

const app = express();
const port = 3000;
const __dirname = path.resolve();

env.config();

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, "../client/dist")));

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "../client/dist/index.html"));
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
