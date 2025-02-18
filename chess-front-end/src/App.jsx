import React, { useState } from "react";
import "./App.css"

function FilterForm({ setFilters }) {
  const [user, setUser] = useState("Elias661");
  const [userRangeMin, setUserRangeMin] = useState("");
  const [userRangeMax, setUserRangeMax] = useState("");
  const [opponentRangeMin, setOpponentRangeMin] = useState("");
  const [opponentRangeMax, setOpponentRangeMax] = useState("");
  const [dateRangeStart, setDateRangeStart] = useState("");
  const [dateRangeEnd, setDateRangeEnd] = useState("");
  const [timeControlMin, setTimeControlMin] = useState("");
  const [timeControlMax, setTimeControlMax] = useState("");
  const [rated, setRated] = useState(false);
  const [playingAsWhite, setPlayingAsWhite] = useState(true);

  // Automatically update filters whenever any field changes
  React.useEffect(() => {
    setFilters({
      user,
      userRangeMin,
      userRangeMax,
      opponentRangeMin,
      opponentRangeMax,
      dateRangeStart,
      dateRangeEnd,
      timeControlMin,
      timeControlMax,
      rated,
      playingAsWhite,
    });
  }, [
    user, userRangeMin, userRangeMax,
    opponentRangeMin, opponentRangeMax,
    dateRangeStart, dateRangeEnd,
    timeControlMin, timeControlMax,
    rated, playingAsWhite,
    setFilters
  ]);

  return (
    <div>
      <h1>Set Filter Info</h1>
      <label>User:
        <input type="text" value={user} onChange={(e) => setUser(e.target.value)} />
      </label>
      <br />

      <label>User Min Rating:
        <input type="number" value={userRangeMin} onChange={(e) => setUserRangeMin(e.target.value)} />
      </label>
      <label>User Max Rating:
        <input type="number" value={userRangeMax} onChange={(e) => setUserRangeMax(e.target.value)} />
      </label>
      <br />

      <label>Opponent Min Rating:
        <input type="number" value={opponentRangeMin} onChange={(e) => setOpponentRangeMin(e.target.value)} />
      </label>
      <label>Opponent Max Rating:
        <input type="number" value={opponentRangeMax} onChange={(e) => setOpponentRangeMax(e.target.value)} />
      </label>
      <br />

      <label>Start Date:
        <input type="date" value={dateRangeStart} onChange={(e) => setDateRangeStart(e.target.value)} />
      </label>
      <label>End Date:
        <input type="date" value={dateRangeEnd} onChange={(e) => setDateRangeEnd(e.target.value)} />
      </label>
      <br />

      <label>Min Time Control:
        <input type="number" value={timeControlMin} onChange={(e) => setTimeControlMin(e.target.value)} />
      </label>
      <label>Max Time Control:
        <input type="number" value={timeControlMax} onChange={(e) => setTimeControlMax(e.target.value)} />
      </label>
      <br />

      <label>Rated:
        <input type="checkbox" checked={rated} onChange={(e) => setRated(e.target.checked)} />
      </label>
      <br />

      <label>Playing as White:
        <input type="checkbox" checked={playingAsWhite} onChange={(e) => setPlayingAsWhite(e.target.checked)} />
      </label>
      <br />
    </div>
  );
}

function RefreshButton({ filters, setApiData }) {
  const handleRefresh = async () => {
    console.log(filters) // Empty??
    try {
      const response = await fetch("http://192.168.1.111:5000/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filters),
      });

      if (!response.ok) throw new Error("API request failed");

      const data = await response.json();
      setApiData(data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  return <button onClick={handleRefresh}>Refresh</button>;
}

function InfoBox({ apiData }) {
  return (
    <div>
      <h2>API Response</h2>
      <pre>{apiData ? apiData.message : "No data available yet. Click Refresh."}</pre>
    </div>
  );
}


function App() {
  const [filters, setFilters] = useState({});
  const [apiData, setApiData] = useState(null);

  return (
    <div>
      <FilterForm setFilters={setFilters} />
      <RefreshButton filters={filters} setApiData={setApiData} />
      <InfoBox apiData={apiData} />
    </div>
  );
}

export default App;
