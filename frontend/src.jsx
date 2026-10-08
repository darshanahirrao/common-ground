import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Download,
  Film,
  LoaderCircle,
  Moon,
  Plus,
  Search,
  Sun,
  ThumbsDown,
  Trash2,
  X,
} from "lucide-react";
import "./style.css";

const seeds = [
  {
    entity_id: "preview-quiet",
    name: "The Lantern House",
    source: "synthetic",
  },
  { entity_id: "preview-action", name: "Orbital Run", source: "synthetic" },
  { entity_id: "preview-offbeat", name: "Paper Streets", source: "synthetic" },
];
const initialPeople = () =>
  ["Asha", "Leo", "Mina"].map((name, i) => ({ name, anchors: [seeds[i]] }));

async function request(path, options) {
  const response = await fetch(path, {
    ...options,
    signal: AbortSignal.timeout(90000),
  });
  const body = await response.json();
  if (!response.ok)
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Check each person and their selected anchors.",
    );
  return body;
}

function FilmArt({ candidate, source }) {
  const [failed, setFailed] = useState(false);
  if (source === "synthetic" && candidate.preview_art !== null) {
    return (
      <div
        className="poster"
        role="img"
        aria-label={`Fictional ${candidate.name} artwork`}
        style={{
          backgroundImage: "url(/preview-films.png)",
          backgroundPosition: `${candidate.preview_art * 50}% center`,
        }}
      />
    );
  }
  if (candidate.image_url && !failed) {
    return (
      <img
        className="poster"
        src={candidate.image_url}
        alt={`${candidate.name} poster`}
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
      />
    );
  }
  return (
    <div className="poster missing-art">
      <Film size={28} />
      <span>Artwork unavailable</span>
    </div>
  );
}

function App() {
  const [source, setSource] = useState("synthetic");
  const [people, setPeople] = useState(initialPeople);
  const [vetoes, setVetoes] = useState([]);
  const [everyone, setEveryone] = useState(true);
  const [plan, setPlan] = useState(null);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [searchPerson, setSearchPerson] = useState(0);
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [theme, setTheme] = useState(
    () =>
      localStorage.getItem("common-ground-theme") ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"),
  );
  const operation = useRef(0);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("common-ground-theme", theme);
  }, [theme]);
  useEffect(() => {
    request("/api/status")
      .then(setStatus)
      .catch(() => setStatus({ qloo_configured: false }));
  }, []);

  function clearResult() {
    operation.current += 1;
    setPlan(null);
    setError("");
    setBusy(false);
  }
  function updatePerson(index, change) {
    setPeople((current) =>
      current.map((person, i) =>
        i === index ? { ...person, ...change } : person,
      ),
    );
    clearResult();
  }
  function changeSource(next) {
    if (next === source) return;
    operation.current += 1;
    setSource(next);
    setPlan(null);
    setVetoes([]);
    setError("");
    setBusy(false);
    setMatches(null);
    setQuery("");
    setSearchError("");
    setPeople(
      next === "synthetic"
        ? initialPeople()
        : people.map((person) => ({ name: person.name, anchors: [] })),
    );
  }
  async function makePlan(nextVetoes = vetoes) {
    const run = ++operation.current;
    setBusy(true);
    setError("");
    try {
      const result = await request("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source,
          members: people,
          veto_ids: nextVetoes.map((v) => v.entity_id),
          require_everyone: everyone,
        }),
      });
      if (run === operation.current) setPlan(result);
    } catch (err) {
      if (run === operation.current) {
        setPlan(null);
        setError(
          err.name === "TimeoutError"
            ? "Planning timed out. Retry the query."
            : err.message,
        );
      }
    } finally {
      if (run === operation.current) setBusy(false);
    }
  }
  async function findAnchors(event) {
    event.preventDefault();
    const currentSource = source;
    const run = operation.current;
    setSearching(true);
    setSearchError("");
    setMatches(null);
    try {
      const result = await request(
        `/api/search?source=${currentSource}&query=${encodeURIComponent(query.trim())}`,
      );
      if (run === operation.current) setMatches(result.results);
    } catch (err) {
      if (run === operation.current) setSearchError(err.message);
    } finally {
      setSearching(false);
    }
  }
  function chooseAnchor(anchor) {
    const person = people[searchPerson];
    if (
      person &&
      person.anchors.length < 3 &&
      !person.anchors.some((a) => a.entity_id === anchor.entity_id)
    ) {
      updatePerson(searchPerson, { anchors: [...person.anchors, anchor] });
    }
    setMatches(null);
    setQuery("");
  }
  function veto(candidate) {
    const next = [
      ...vetoes,
      { entity_id: candidate.entity_id, name: candidate.name },
    ];
    setVetoes(next);
    makePlan(next);
  }
  function download() {
    const link = document.createElement("a");
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(plan, null, 2)], { type: "application/json" }),
    );
    link.href = url;
    link.download = `common-ground-${source}-evidence.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  const ready =
    people.length >= 2 &&
    people.every((person) => person.name.trim() && person.anchors.length);
  const top = plan?.candidates?.[0];

  return (
    <>
      <header className="topbar">
        <a className="wordmark" href="/">
          Common Ground<span>Movie night</span>
        </a>
        <div className="header-tools">
          <div className="segmented" role="group" aria-label="Data source">
            <button
              aria-pressed={source === "synthetic"}
              onClick={() => changeSource("synthetic")}
            >
              Preview
            </button>
            <button
              aria-pressed={source === "qloo"}
              onClick={() => changeSource("qloo")}
            >
              Qloo Live
            </button>
          </div>
          <button
            className="icon-button"
            title="Switch color theme"
            aria-label="Switch color theme"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>
      </header>
      <main className="workspace">
        <aside className="group-panel" aria-labelledby="group-heading">
          <div className="section-heading">
            <h1 id="group-heading">Tonight's group</h1>
            <span>{people.length} people</span>
          </div>
          <div className="people">
            {people.map((person, index) => (
              <section className="person" key={index}>
                <div className="person-name">
                  <label htmlFor={`person-${index}`}>Person {index + 1}</label>
                  <button
                    className="icon-button"
                    title={`Remove person ${index + 1}`}
                    aria-label={`Remove person ${index + 1}`}
                    disabled={people.length <= 2}
                    onClick={() => {
                      setPeople(people.filter((_, i) => i !== index));
                      setSearchPerson(0);
                      setMatches(null);
                      clearResult();
                    }}
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
                <input
                  id={`person-${index}`}
                  maxLength={40}
                  value={person.name}
                  onChange={(e) =>
                    updatePerson(index, { name: e.target.value })
                  }
                />
                <ul
                  className="anchor-list"
                  role="list"
                  aria-label={`${person.name || "Person"} cultural anchors`}
                >
                  {person.anchors.map((anchor) => (
                    <li key={anchor.entity_id}>
                      <Film size={16} />
                      <span>{anchor.name}</span>
                      <button
                        className="icon-button"
                        title={`Remove ${anchor.name}`}
                        aria-label={`Remove ${anchor.name}`}
                        onClick={() =>
                          updatePerson(index, {
                            anchors: person.anchors.filter(
                              (a) => a.entity_id !== anchor.entity_id,
                            ),
                          })
                        }
                      >
                        <X size={15} />
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
          <button
            className="quiet-button"
            disabled={people.length >= 6}
            onClick={() => {
              setPeople([
                ...people,
                { name: `Guest ${people.length + 1}`, anchors: [] },
              ]);
              clearResult();
            }}
          >
            <Plus size={17} />
            Add person
          </button>
          <form className="anchor-search" onSubmit={findAnchors}>
            <label htmlFor="anchor-person">Add taste anchor for</label>
            <select
              id="anchor-person"
              value={searchPerson}
              onChange={(e) => {
                setSearchPerson(Number(e.target.value));
                setMatches(null);
              }}
            >
              {people.map((person, i) => (
                <option key={i} value={i}>
                  {person.name || `Person ${i + 1}`}
                </option>
              ))}
            </select>
            <label htmlFor="anchor-query">
              Film, artist or cultural favorite
            </label>
            <div className="search-row">
              <input
                id="anchor-query"
                value={query}
                minLength={2}
                maxLength={100}
                required
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                type="submit"
                className="icon-button"
                title="Search anchors"
                aria-label="Search anchors"
                disabled={
                  searching || people[searchPerson]?.anchors.length >= 3
                }
              >
                {searching ? (
                  <LoaderCircle className="spin" size={19} />
                ) : (
                  <Search size={19} />
                )}
              </button>
            </div>
            {searchError && (
              <p className="error" role="alert">
                {searchError}
              </p>
            )}
            {matches && (
              <ul
                className="search-results"
                role="list"
                aria-label="Anchor matches"
              >
                {matches.length ? (
                  matches.map((anchor) => (
                    <li key={anchor.entity_id}>
                      <button
                        type="button"
                        disabled={people[searchPerson]?.anchors.some(
                          (a) => a.entity_id === anchor.entity_id,
                        )}
                        onClick={() => chooseAnchor(anchor)}
                      >
                        {anchor.name}
                        <Plus size={16} />
                      </button>
                    </li>
                  ))
                ) : (
                  <li>No matching anchors.</li>
                )}
              </ul>
            )}
          </form>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={everyone}
              onChange={(e) => {
                setEveryone(e.target.checked);
                clearResult();
              }}
            />
            Evidence for everyone
          </label>
          <button
            className="primary-button"
            disabled={!ready || busy}
            onClick={() => makePlan()}
          >
            {busy ? (
              <LoaderCircle size={18} className="spin" />
            ) : (
              <Film size={18} />
            )}
            {busy ? "Finding common ground" : "Find a shared film"}
          </button>
        </aside>
        <section className="results-panel" aria-labelledby="results-heading">
          <div className="section-heading">
            <h2 id="results-heading">The shared pick</h2>
            <span className="source-state">
              {source === "synthetic"
                ? "Fictional preview"
                : plan?.source === "qloo"
                  ? "Live Qloo"
                  : status?.qloo_configured
                    ? "Qloo key configured, validation pending"
                    : "Qloo key pending"}
            </span>
          </div>
          {source === "synthetic" && (
            <p className="source-notice">
              Fictional films and rankings. No live Qloo data.
            </p>
          )}
          {error && (
            <div className="error-state" role="alert">
              <h3>Live planning unavailable</h3>
              <p>{error}</p>
            </div>
          )}
          {!plan && !error && (
            <div className="empty-state">
              <Film size={38} />
              <h3>One film. Everyone considered.</h3>
            </div>
          )}
          {plan && (
            <div className={busy ? "result-content pending" : "result-content"}>
              <div className="result-summary">
                <div>
                  <h3>{top ? top.name : "No shared evidence yet"}</h3>
                  <p>
                    {top
                      ? `${top.coverage} of ${people.length} people represented`
                      : "No returned film has evidence for every person."}
                  </p>
                </div>
                <button
                  className="icon-button"
                  title="Download evidence"
                  aria-label="Download evidence"
                  onClick={download}
                  disabled={busy}
                >
                  <Download size={20} />
                </button>
              </div>
              <div className="candidate-list">
                {plan.candidates.map((candidate, index) => (
                  <article className="candidate" key={candidate.entity_id}>
                    <FilmArt candidate={candidate} source={source} />
                    <div className="candidate-info">
                      <div className="candidate-heading">
                        <div>
                          <span className="candidate-label">
                            {index === 0 ? "Shared pick" : "Alternative"}
                          </span>
                          <h3>{candidate.name}</h3>
                        </div>
                        <button
                          className="icon-button"
                          title={`Veto ${candidate.name}`}
                          aria-label={`Veto ${candidate.name}`}
                          disabled={busy}
                          onClick={() => veto(candidate)}
                        >
                          <ThumbsDown size={18} />
                        </button>
                      </div>
                      <div className="rank-table">
                        <table>
                          <caption>Per-person recommendation rank</caption>
                          <thead>
                            <tr>
                              <th scope="col">Person</th>
                              <th scope="col">Rank</th>
                              <th scope="col">Evidence</th>
                            </tr>
                          </thead>
                          <tbody>
                            {candidate.evidence.map((row) => (
                              <tr key={row.person}>
                                <th scope="row">{row.person}</th>
                                <td>{row.rank ?? "Not returned"}</td>
                                <td>{row.rank ? "Present" : "Missing"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
              {plan.average_first_pick &&
                top &&
                plan.average_first_pick.entity_id !== top.entity_id && (
                  <section className="tradeoff">
                    <h3>Average-first comparison</h3>
                    <p>
                      {plan.average_first_pick.name} has the highest average
                      rank score. {top.name} has stronger evidence for the
                      least-supported person, or prioritizes broader coverage
                      when some evidence is missing.
                    </p>
                  </section>
                )}
              <details className="evidence">
                <summary>Query evidence</summary>
                <p>{plan.method}</p>
                <p>{plan.uncertainty}</p>
                <ol>
                  {plan.query_steps.map((step, i) => (
                    <li key={i}>
                      <strong>{step.person}</strong>
                      <span>
                        {step.returned} results, page {step.page}
                      </span>
                      <code>{step.endpoint}</code>
                    </li>
                  ))}
                </ol>
                <p className="timestamp">
                  {new Date(plan.generated_at).toLocaleString()}
                </p>
              </details>
            </div>
          )}
          {vetoes.length > 0 && (
            <section className="veto-list">
              <h3>Vetoed films</h3>
              <ul role="list">
                {vetoes.map((item) => (
                  <li key={item.entity_id}>
                    <span>{item.name}</span>
                    <button
                      className="icon-button"
                      title={`Restore ${item.name}`}
                      aria-label={`Restore ${item.name}`}
                      onClick={() => {
                        setVetoes(
                          vetoes.filter((v) => v.entity_id !== item.entity_id),
                        );
                        clearResult();
                      }}
                    >
                      <X size={16} />
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </section>
      </main>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
