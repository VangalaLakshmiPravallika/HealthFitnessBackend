const express = require("express");
const axios = require("axios");
const cors = require("cors");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors({
  origin: "*", // Allow all origins (for testing)
  methods: ["GET"],
}));
app.use(express.json());

// NewsAPI Configuration
const NEWS_API_KEY = process.env.NEWS_API_KEY; // Ensure this is set in your .env file
const NEWS_API_URL = "https://newsapi.org/v2/everything";

// Endpoint to fetch health and fitness news
app.get("/api/news", async (req, res) => {
  try {
    const query = "health fitness diet"; // Search query for health, fitness, and diet news
    const response = await axios.get(NEWS_API_URL, {
      params: {
        q: query,
        sortBy: "publishedAt",
        pageSize: 10, // Number of articles to fetch
        apiKey: NEWS_API_KEY,
      },
    });

    // Send the news articles to the client
    res.json(response.data.articles);
  } catch (error) {
    console.error("Error fetching news:", error.message);

    // Log the full error response for debugging
    if (error.response) {
      console.error("Error response data:", error.response.data);
      console.error("Error response status:", error.response.status);
      console.error("Error response headers:", error.response.headers);
    }

    res.status(500).json({
      error: "Failed to fetch news",
      details: error.message,
    });
  }
});

// Default route
app.get("/", (req, res) => {
  res.send("Health and Fitness Backend is running!");
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});