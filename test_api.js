// Node.js dynamic fetch import
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

// Function to call your /predict endpoint
const getSuggestedTasks = async (pattern, subtraction, income) => {
  const response = await fetch('https://mathtatag-api.onrender.com/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pattern_score: pattern,
      subtraction_score: subtraction,
      income_bracket: income
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Unknown error');
  }

  const result = await response.json();
  return result;
};

// Run and test the function
(async () => {
  try {
    const pattern = 6;
    const subtraction = 5;
    const income = 3;
    const tasks = await getSuggestedTasks(pattern, subtraction, income);
    console.log('✅ Suggested tasks:\n', tasks);
  } catch (err) {
    console.error('❌ API error:', err.message);
  }
})();
