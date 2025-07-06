const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const getSuggestedTasks = async (pattern, subtraction, income) => {
  const response = await fetch('http://127.0.0.1:5000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pattern_score: pattern,
      subtraction_score: subtraction,
      income_bracket: income
    }),
  });
a
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Unknown error');
  }

  const result = await response.json();
  return result;
};

(async () => {
  try {
    // Change these values to test different inputs
    const pattern = 6;
    const subtraction = 5;
    const income = 3;
    const tasks = await getSuggestedTasks(pattern, subtraction, income);
    console.log('Suggested tasks:', tasks);
  } catch (err) {
    console.error('API error:', err.message);
  }
})(); 