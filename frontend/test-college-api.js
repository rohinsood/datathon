// Test script for the college advisor API
const testQueries = [
  "Best value colleges in Texas",
  "Most affordable colleges",
  "Colleges with high graduation rates in California",
  "What are the top engineering schools?"
];

async function testAPI() {
  console.log("Testing College Advisor API...\n");
  
  for (const query of testQueries) {
    try {
      console.log(`Query: "${query}"`);
      
      const response = await fetch('http://localhost:3000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: query }),
      });
      
      const data = await response.json();
      console.log(`Response: ${data.response.substring(0, 200)}...\n`);
      
    } catch (error) {
      console.error(`Error testing "${query}":`, error.message);
    }
  }
}

// Run if Ollama is available
fetch('http://localhost:11434/api/tags')
  .then(() => {
    console.log("Ollama is running, testing API...");
    testAPI();
  })
  .catch(() => {
    console.log("Ollama is not running. Please run: ./setup-ollama.sh");
  });