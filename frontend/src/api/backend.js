import axios from "axios";

// Set your Render backend URL here
const API_BASE = "https://ai-difference-checker-6.onrender.com/api";

// Function to upload two documents
export const uploadDocuments = async (fileA, fileB) => {
  try {
    const formData = new FormData();
    formData.append("file_a", fileA);
    formData.append("file_b", fileB);

    const response = await axios.post(`${API_BASE}/upload`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error uploading documents:", error.response || error.message);
    throw error;
  }
};

// Function to get AI summary for a diff
export const getSummary = async (diffText) => {
  try {
    const response = await axios.post(`${API_BASE}/summary`, { diff: diffText });
    return response.data;
  } catch (error) {
    console.error("Error getting summary:", error.response || error.message);
    throw error;
  }
};
