import React, { useState } from "react";
import "./App.css"
import { useActionState } from "react";

function FilterForm({ setFilters }) {
  const [user, setUser] = useState("Elias661");
  const [userRangeMin, setUserRangeMin] = useState("0");
  const [userRangeMax, setUserRangeMax] = useState("3000");
  const [opponentRangeMin, setOpponentRangeMin] = useState("0");
  const [opponentRangeMax, setOpponentRangeMax] = useState("3000");
  const [dateRangeStart, setDateRangeStart] = useState("2000-01-01");
  const [dateRangeEnd, setDateRangeEnd] = useState("2099-01-01");
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
      console.log('Got data ', data)
      setApiData(data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  return <button onClick={handleRefresh}>Refresh All</button>;
}

function UpdateDBButton(user) {
  // const [user] = user
  const [responseText, setResponseText] = useState('Database not updated')
  const handleRefresh = async () => {
    setResponseText("Updating database...")
    try {
      const response = await fetch("http://192.168.1.111:5000/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(user),
      });

      if (!response.ok) throw new Error("API request failed");

      const data = await response.json();
      setResponseText(data.message);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  return (
    <div>
      <button onClick={handleRefresh}>Update DB</button>
      <h3>{responseText}</h3>
    </div>
  );
}

function InfoBox({ apiData, title, filters }) {
  // Make sure apiData.get_most_played_players is an array
  const players = apiData?.games_played_against_player || [];
  return (
    <div>
      <h2>{title}</h2>
      <pre>{apiData ? apiData.message : "No data available yet. Click Refresh."}</pre>
      
      {/* Scrollable container */}
      <div style={{ maxHeight: '200px', overflowY: 'scroll', border: '1px solid #ccc', padding: '8px' }}>
        {players.map((item, index) => {
          // Assuming item is an object with key-value pairs:
          return (
            <div key={index} style={{ marginBottom: '4px' }}>
              {Object.entries(item).map(([key, value]) => (
                <div key={key}>
                  <strong>{key}</strong>: {value}
                </div>
              ))}
            </div>
          );
        })}
      </div>
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
      <UpdateDBButton user={filters.user}></UpdateDBButton>
      <InfoBox apiData={apiData} title='Most played players' filters={filters} />
    </div>
  );
}

export default App;
