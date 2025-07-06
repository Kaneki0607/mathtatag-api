const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const askGpt = async (prompt) => {
  const response = await fetch('http://127.0.0.1:5000/gpt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    let error, text;
    try {
      error = await response.json();
    } catch {
      error = {};
    }
    try {
      text = await response.text();
    } catch {
      text = '';
    }
    throw new Error((error.error || text || 'Unknown error') + (error.details ? ('\nDetails: ' + error.details) : ''));
  }

  const result = await response.json();
  return result.response;
};

(async () => {
  try {
    const prompt = `Ako ay isang guro ng Grade 1. Tulungan mo akong gumawa ng malinaw, makabuluhan, at suportadong payo para sa magulang ng batang si Lloyd. Narito ang impormasyon tungkol sa kanya:
                    May score siyang 8/10 sa pattern recognition at 9/10 sa subtraction (mga bilang hanggang 100).
                    Nakapagtala siya ng 28% improvement mula sa kanyang pretest score.
                    Narito rin ang mga home-based tasks na ibinigay ng magulang para suportahan ang kanyang pagkatuto:
                    - Takip Number Game – Gamit ang takip, ipinapaskil ang bilang 1–10, pagkatapos ay inaalis ang ilan at pinapabilang ang natira. Layunin: Makita sa aktwal ang konsepto ng pagbawas.
                    - Pag-match ng Pattern gamit ang Papel – Gupitin ang iba't ibang hugis at kulay mula sa colored paper at bumuo ng pattern. Layunin: Palakasin ang kakayahan sa pagsunod sa pattern.
                    - Karton Subtraction Board – Gumamit ng karton at bato/buto bilang counters para sa subtraction. Layunin: Mapalawak ang biswal na pang-unawa sa pagbawas.
                    - Pagbawas gamit ang Laruan – Maglaro gamit ang 10 laruan, alisin ang ilan batay sa tanong, at bilangin ang natira. Layunin: Maisabuhay ang konsepto ng pagbawas.
                    - Pagguhit ng Hugis gamit ang Karton – Gumuhit ng pattern gamit ang mga hugis mula sa recycled cardboard. Layunin: Pagtibayin ang kakayahang makakita ng pattern.
                    - Dahon Matching – Pagtapat-tapatin ang mga dahon base sa hugis at laki. Layunin: Mahasa ang visual discrimination.
                    Bilang guro, nais kong bigyan ng positibong feedback ang magulang, at magrekomenda ng dagdag na gabay para lalo pang mapalago ang kakayahan ni Lloyd. Gusto ko rin ng mga mungkahi kung paano mapanatili ang kanyang motivation at interest habang nag-aaral sa bahay. Gamitin ang wika ng isang guro na nagbibigay-gabay at suporta sa magulang na aktibong nakikibahagi sa pagkatuto ng kanilang anak. Gawing straight forward ang payo at isang paragraph lamang`;

    const answer = await askGpt(prompt);
    console.log('GPT response:', answer);
  } catch (err) {
    console.error('API error:', err.message);
  }
})(); 