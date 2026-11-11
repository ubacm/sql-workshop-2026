// =====================================================================
// Tunes frontend: plain JavaScript, no build step.
// Every piece of data comes from the Flask API, which calls queries.py.
// If a query isn't written yet, that part of the page says so.
// =====================================================================

const page = document.getElementById("page");
const modal = document.getElementById("modal");

let currentUserId = Number(readStorage("tunes-user") || 1);
let songFilters = { search: "", genre: "" };


// ---------------------------------------------------------------------
// API helper: every request goes through here and gets added to the SQL log
// ---------------------------------------------------------------------

class ApiError extends Error {
    constructor(payload, status) {
        super(payload.message || `Request failed (${status})`);
        this.payload = payload;
        this.status = status;
    }
    get notImplemented() {
        return this.payload.error === "not_implemented";
    }
}

async function api(method, path, body) {
    const options = { method, headers: {} };
    if (body !== undefined) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }

    const response = await fetch(path, options);
    let payload;
    try {
        payload = await response.json();
    } catch (error) {
        payload = { error: "server", message: `Server error (${response.status}). Check the terminal running app.py.` };
    }

    addLogEntry(method, path, response.status, payload);

    if (!response.ok) {
        throw new ApiError(payload, response.status);
    }
    return payload.data;
}


// ---------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function formatDuration(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined) return "";
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = String(Math.round(totalSeconds % 60)).padStart(2, "0");
    return `${minutes}:${seconds}`;
}

function colorFor(text) {
    let hash = 0;
    for (const character of String(text)) {
        hash = (hash * 31 + character.charCodeAt(0)) % 360;
    }
    return `hsl(${hash}, 65%, 62%)`;
}

function readStorage(key) {
    try {
        return localStorage.getItem(key);
    } catch (error) {
        return null;
    }
}

function writeStorage(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (error) {
        // Storage unavailable; the setting just won't be remembered.
    }
}

// The yellow "not implemented" card or red error card shown in place of data.
function stateCard(error) {
    const payload = error.payload || { message: String(error) };

    if (error.notImplemented) {
        return `
            <div class="state todo">
                <div class="state-title">🛠 Not implemented yet</div>
                Write the SQL for <code>${escapeHtml(payload.function)}</code> in <b>queries.py</b>, save, and refresh.
            </div>`;
    }

    let explanation = "";
    if (payload.error === "integrity") {
        explanation = "<br>The database blocked this change because it would break a rule in schema.sql " +
                      "(a FOREIGN KEY, PRIMARY KEY or UNIQUE constraint).";
    }
    const sqlBlock = payload.sql ? `<pre>${escapeHtml(payload.sql)}</pre>` : "";
    const functionName = payload.function ? ` in <code>${escapeHtml(payload.function)}</code>` : "";
    return `
        <div class="state error">
            <div class="state-title">💥 Error${functionName}</div>
            ${escapeHtml(payload.message)}${explanation}
            ${sqlBlock}
        </div>`;
}

function emptyCard(message) {
    return `<div class="state empty">${escapeHtml(message)}</div>`;
}

// Loads data into one section of a page. If the query isn't written yet
// (or has a bug), only this section shows the problem; the rest of the page still works.
async function loadSection(container, loadData, render) {
    container.innerHTML = `<div class="state loading">Loading…</div>`;
    try {
        const data = await loadData();
        render(container, data);
    } catch (error) {
        container.innerHTML = stateCard(error);
    }
}

// Generic table. columns = [{ label, value: (row) => html, className }]
function tableHtml(columns, rows, rowActions) {
    const headerCells = columns
        .map((column) => `<th class="${column.className || ""}">${escapeHtml(column.label)}</th>`)
        .join("");
    const actionHeader = rowActions ? "<th></th>" : "";

    const bodyRows = rows.map((row, index) => {
        const cells = columns
            .map((column) => `<td class="${column.className || ""}">${column.value(row, index)}</td>`)
            .join("");
        const actions = rowActions ? `<td class="actions">${rowActions(row)}</td>` : "";
        return `<tr>${cells}${actions}</tr>`;
    }).join("");

    return `
        <div class="table-wrap">
            <table>
                <thead><tr>${headerCells}${actionHeader}</tr></thead>
                <tbody>${bodyRows}</tbody>
            </table>
        </div>`;
}


// ---------------------------------------------------------------------
// Toasts and actions (create / update / delete)
// ---------------------------------------------------------------------

function toast(message, kind = "success") {
    const element = document.createElement("div");
    element.className = `toast ${kind}`;
    element.textContent = message;
    document.getElementById("toasts").appendChild(element);
    setTimeout(() => element.remove(), kind === "success" ? 2500 : 6000);
}

function toastError(error) {
    if (error.notImplemented) {
        toast(`🛠 ${error.payload.function} isn't written yet. Add the SQL in queries.py.`, "todo");
    } else {
        toast(`💥 ${error.message}`, "error");
    }
}

// Runs a write action, then shows a toast and refreshes the page.
async function runAction(action, successMessage) {
    try {
        await action();
        toast(successMessage);
        renderCurrentRoute();
    } catch (error) {
        toastError(error);
    }
}


// ---------------------------------------------------------------------
// Modal forms
// ---------------------------------------------------------------------

function fieldHtml(field) {
    const value = escapeHtml(field.value ?? "");
    const required = field.required === false ? "" : "required";
    let input;

    if (field.type === "select") {
        const options = field.options.map((option) => {
            const selected = String(option.value) === String(field.value) ? "selected" : "";
            return `<option value="${escapeHtml(option.value)}" ${selected}>${escapeHtml(option.label)}</option>`;
        }).join("");
        input = `<select name="${field.name}" ${required}>${options}</select>`;
    } else {
        const listAttribute = field.suggestions ? `list="${field.name}-suggestions"` : "";
        const datalist = field.suggestions
            ? `<datalist id="${field.name}-suggestions">${field.suggestions.map((s) => `<option value="${escapeHtml(s)}">`).join("")}</datalist>`
            : "";
        const min = field.min !== undefined ? `min="${field.min}"` : "";
        input = `<input name="${field.name}" type="${field.type || "text"}" value="${value}" ${min} ${listAttribute} ${required}>${datalist}`;
    }

    const help = field.help ? `<span class="help">${escapeHtml(field.help)}</span>` : "";
    return `<label>${escapeHtml(field.label)}${input}${help}</label>`;
}

// Opens a form in a dialog. onSubmit receives the form values;
// if it throws, the error is shown inside the dialog and the dialog stays open.
function openForm({ title, fields = [], intro = "", submitLabel = "Save", danger = false, onSubmit }) {
    modal.innerHTML = `
        <h3>${escapeHtml(title)}</h3>
        <form>
            ${intro ? `<div class="muted">${intro}</div>` : ""}
            ${fields.map(fieldHtml).join("")}
            <div class="form-error"></div>
            <div class="modal-actions">
                <button type="button" class="button ghost" data-close>Cancel</button>
                <button type="submit" class="button ${danger ? "danger" : "primary"}">${escapeHtml(submitLabel)}</button>
            </div>
        </form>`;

    const form = modal.querySelector("form");
    modal.querySelector("[data-close]").addEventListener("click", () => modal.close());

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const values = Object.fromEntries(new FormData(form));
        try {
            await onSubmit(values);
            modal.close();
        } catch (error) {
            modal.querySelector(".form-error").innerHTML = stateCard(error);
        }
    });

    modal.showModal();
}

function openErrorDialog(title, error) {
    modal.innerHTML = `
        <h3>${escapeHtml(title)}</h3>
        ${stateCard(error)}
        <div class="modal-actions"><button class="button" data-close>Close</button></div>`;
    modal.querySelector("[data-close]").addEventListener("click", () => modal.close());
    modal.showModal();
}


// ---------------------------------------------------------------------
// Router: #/songs, #/artists/3, #/playlists/2, ...
// ---------------------------------------------------------------------

function renderCurrentRoute() {
    const parts = location.hash.replace(/^#\/?/, "").split("/");
    const section = parts[0] || "songs";
    const id = parts[1] ? Number(parts[1]) : null;

    for (const link of document.querySelectorAll(".nav a")) {
        link.classList.toggle("active", link.dataset.page === section);
    }

    if (section === "songs") renderSongsPage();
    else if (section === "artists" && id) renderArtistPage(id);
    else if (section === "artists") renderArtistsPage();
    else if (section === "playlists" && id) renderPlaylistPage(id);
    else if (section === "playlists") renderPlaylistsPage();
    else if (section === "charts") renderChartsPage();
    else if (section === "users") renderUsersPage();
    else if (section === "database") renderDatabasePage();
    else if (section === "freeplay") renderFreePlayPage();
    else renderSongsPage();
}


// =====================================================================
// SONGS PAGE
// =====================================================================

function renderSongsPage() {
    page.innerHTML = `
        <div class="page-header">
            <div>
                <h1>Songs</h1>
                <div class="subtitle">Your whole library</div>
            </div>
            <div class="header-actions">
                <button class="button primary" id="new-song">+ New song</button>
            </div>
        </div>
        <div class="toolbar">
            <input type="search" id="song-search" placeholder="Search songs or artists…" value="${escapeHtml(songFilters.search)}">
            <select id="genre-filter"><option value="">All genres</option></select>
        </div>
        <div id="songs-table"></div>`;

    loadGenreFilter();

    let searchTimer = null;
    document.getElementById("song-search").addEventListener("input", (event) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            songFilters.search = event.target.value.trim();
            loadSongsTable();
        }, 300);
    });
    document.getElementById("genre-filter").addEventListener("change", (event) => {
        songFilters.genre = event.target.value;
        loadSongsTable();
    });
    document.getElementById("new-song").addEventListener("click", openNewSongForm);
    document.getElementById("songs-table").addEventListener("click", handleSongAction);

    loadSongsTable();
}

async function loadGenreFilter() {
    const select = document.getElementById("genre-filter");
    try {
        const genres = await api("GET", "/api/genres");
        for (const row of genres) {
            const selected = row.genre === songFilters.genre ? "selected" : "";
            select.insertAdjacentHTML("beforeend",
                `<option value="${escapeHtml(row.genre)}" ${selected}>${escapeHtml(row.genre)}</option>`);
        }
    } catch (error) {
        select.innerHTML = `<option value="">Genres: ${error.notImplemented ? "list_genres() not written" : "error"}</option>`;
        select.disabled = true;
    }
}

function loadSongsTable() {
    const params = new URLSearchParams();
    if (songFilters.search) params.set("q", songFilters.search);
    else if (songFilters.genre) params.set("genre", songFilters.genre);
    const path = params.toString() ? `/api/songs?${params}` : "/api/songs";

    loadSection(document.getElementById("songs-table"), () => api("GET", path), (container, songs) => {
        if (songs.length === 0) {
            container.innerHTML = emptyCard("No songs match.");
            return;
        }
        container.innerHTML = songsTableHtml(songs) +
            `<div class="table-footer">${songs.length} songs</div>`;
    });
}

function songsTableHtml(songs, showArtist = true) {
    const columns = [
        { label: "", value: (song) => `<button class="icon-button play" data-action="play" data-id="${song.id}" data-title="${escapeHtml(song.title)}" title="Play">▶</button>` },
        { label: "Title", className: "title", value: (song) => escapeHtml(song.title) },
    ];
    if (showArtist) {
        columns.push({ label: "Artist", value: (song) => escapeHtml(song.artist) });
    }
    columns.push(
        { label: "Album", value: (song) => escapeHtml(song.album) },
        { label: "Genre", value: (song) => `<span class="genre-tag">${escapeHtml(song.genre)}</span>` },
        { label: "Time", className: "number", value: (song) => formatDuration(song.duration_sec) },
    );
    const actions = (song) => {
        const data = `data-id="${song.id}" data-title="${escapeHtml(song.title)}" data-genre="${escapeHtml(song.genre)}" data-duration="${song.duration_sec}"`;
        return `
            <button class="icon-button" data-action="add-to-playlist" ${data} title="Add to playlist">＋</button>
            <button class="icon-button" data-action="edit" ${data} title="Edit">✎</button>
            <button class="icon-button delete" data-action="delete" ${data} title="Delete">🗑</button>`;
    };
    return tableHtml(columns, songs, actions);
}

// One click handler for every button in a songs table (used on the Songs and Artist pages).
function handleSongAction(event) {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const song = {
        id: Number(button.dataset.id),
        title: button.dataset.title,
        genre: button.dataset.genre,
        duration_sec: Number(button.dataset.duration),
    };

    if (button.dataset.action === "play") playSong(song);
    if (button.dataset.action === "add-to-playlist") openAddToPlaylistForm(song);
    if (button.dataset.action === "edit") openEditSongForm(song);
    if (button.dataset.action === "delete") openDeleteSongForm(song);
}

async function playSong(song) {
    try {
        await api("POST", `/api/songs/${song.id}/play`, { user_id: currentUserId });
        toast(`▶ Now playing "${song.title}"`);
    } catch (error) {
        toastError(error);
    }
}

async function genreSuggestions() {
    try {
        const genres = await api("GET", "/api/genres");
        return genres.map((row) => row.genre);
    } catch (error) {
        return [];
    }
}

async function openNewSongForm() {
    let albums;
    try {
        albums = await api("GET", "/api/albums");
    } catch (error) {
        openErrorDialog("New song", error);
        return;
    }

    openForm({
        title: "New song",
        submitLabel: "Create song",
        fields: [
            { name: "album_id", label: "Album", type: "select",
              options: albums.map((album) => ({ value: album.id, label: `${album.artist} — ${album.title} (${album.release_year})` })) },
            { name: "title", label: "Title" },
            { name: "genre", label: "Genre", suggestions: await genreSuggestions() },
            { name: "duration_sec", label: "Length (seconds)", type: "number", min: 1, value: 200 },
        ],
        onSubmit: async (values) => {
            const result = await api("POST", "/api/songs", values);
            toast(`Created "${values.title}" (id ${result.new_id})`);
            renderCurrentRoute();
        },
    });
}

async function openEditSongForm(song) {
    openForm({
        title: "Edit song",
        fields: [
            { name: "title", label: "Title", value: song.title },
            { name: "genre", label: "Genre", value: song.genre, suggestions: await genreSuggestions() },
            { name: "duration_sec", label: "Length (seconds)", type: "number", min: 1, value: song.duration_sec },
        ],
        onSubmit: async (values) => {
            await api("PUT", `/api/songs/${song.id}`, values);
            toast("Song updated");
            renderCurrentRoute();
        },
    });
}

function openDeleteSongForm(song) {
    openForm({
        title: "Delete song?",
        intro: `"${escapeHtml(song.title)}" will be removed, along with its plays and playlist entries.`,
        submitLabel: "Delete",
        danger: true,
        onSubmit: async () => {
            await api("DELETE", `/api/songs/${song.id}`);
            toast("Song deleted");
            renderCurrentRoute();
        },
    });
}

async function openAddToPlaylistForm(song) {
    let playlists;
    try {
        playlists = await api("GET", "/api/playlists");
    } catch (error) {
        openErrorDialog("Add to playlist", error);
        return;
    }

    openForm({
        title: `Add "${song.title}" to…`,
        submitLabel: "Add",
        fields: [{
            name: "playlist_id", label: "Playlist", type: "select",
            options: playlists.map((playlist) => ({ value: playlist.id, label: `${playlist.name} (${playlist.owner})` })),
        }],
        onSubmit: async (values) => {
            await api("POST", `/api/playlists/${values.playlist_id}/songs`, { song_id: song.id });
            toast("Added to playlist");
        },
    });
}


// =====================================================================
// ARTISTS PAGES
// =====================================================================

function renderArtistsPage() {
    page.innerHTML = `
        <div class="page-header">
            <div><h1>Artists</h1></div>
            <div class="header-actions"><button class="button primary" id="new-artist">+ New artist</button></div>
        </div>
        <div id="artists-grid"></div>`;

    document.getElementById("new-artist").addEventListener("click", () => openArtistForm(null));

    loadSection(document.getElementById("artists-grid"), () => api("GET", "/api/artists"), (container, artists) => {
        const cards = artists.map((artist) => `
            <a class="card" href="#/artists/${artist.id}">
                <div class="avatar" style="background:${colorFor(artist.name)}">${escapeHtml(artist.name.charAt(0))}</div>
                <div class="card-title">${escapeHtml(artist.name)}</div>
                <div class="card-sub">${escapeHtml(artist.country)} · since ${escapeHtml(artist.formed_year)}</div>
            </a>`).join("");
        container.innerHTML = `<div class="card-grid">${cards}</div>`;
    });
}

function renderArtistPage(artistId) {
    page.innerHTML = `
        <a class="back-link" href="#/artists">← All artists</a>
        <div id="artist-header"></div>
        <h2>Songs</h2>
        <div id="artist-songs"></div>`;

    document.getElementById("artist-songs").addEventListener("click", handleSongAction);

    loadSection(document.getElementById("artist-header"), () => api("GET", `/api/artists/${artistId}`), (container, artist) => {
        container.innerHTML = `
            <div class="page-header">
                <div>
                    <div class="eyebrow">Artist</div>
                    <h1>${escapeHtml(artist.name)}</h1>
                    <div class="subtitle">${escapeHtml(artist.country)} · formed ${escapeHtml(artist.formed_year)}</div>
                </div>
                <div class="header-actions">
                    <button class="button" id="edit-artist">Edit</button>
                    <button class="button danger" id="delete-artist">Delete</button>
                </div>
            </div>`;
        document.getElementById("edit-artist").addEventListener("click", () => openArtistForm(artist));
        document.getElementById("delete-artist").addEventListener("click", () => openDeleteArtistForm(artist));
    });

    loadSection(document.getElementById("artist-songs"), () => api("GET", `/api/artists/${artistId}/songs`), (container, songs) => {
        if (songs.length === 0) {
            container.innerHTML = emptyCard("No songs yet.");
            return;
        }
        container.innerHTML = songsTableHtml(songs, false);
    });
}

// artist = null for "New artist", or an existing artist for "Edit"
function openArtistForm(artist) {
    const isNew = artist === null;
    openForm({
        title: isNew ? "New artist" : "Edit artist",
        submitLabel: isNew ? "Create artist" : "Save",
        fields: [
            { name: "name", label: "Name", value: isNew ? "" : artist.name },
            { name: "country", label: "Country", value: isNew ? "" : artist.country },
            { name: "formed_year", label: "Formed (year)", type: "number", value: isNew ? 2024 : artist.formed_year },
        ],
        onSubmit: async (values) => {
            if (isNew) {
                const result = await api("POST", "/api/artists", values);
                toast(`Created ${values.name}`);
                location.hash = `#/artists/${result.new_id}`;
            } else {
                await api("PUT", `/api/artists/${artist.id}`, values);
                toast("Artist updated");
                renderCurrentRoute();
            }
        },
    });
}

function openDeleteArtistForm(artist) {
    openForm({
        title: "Delete artist?",
        intro: `Delete <b>${escapeHtml(artist.name)}</b>? This can't be undone.`,
        submitLabel: "Delete",
        danger: true,
        onSubmit: async () => {
            await api("DELETE", `/api/artists/${artist.id}`);
            toast(`Deleted ${artist.name}`);
            location.hash = "#/artists";
        },
    });
}


// =====================================================================
// PLAYLISTS PAGES
// =====================================================================

const PLAYLIST_EMOJI = ["🎧", "🔥", "🌙", "☀️", "🚗", "📚", "🌧️", "💃", "🎸", "✨"];

function renderPlaylistsPage() {
    page.innerHTML = `
        <div class="page-header">
            <div><h1>Playlists</h1></div>
            <div class="header-actions"><button class="button primary" id="new-playlist">+ New playlist</button></div>
        </div>
        <div id="playlists-grid"></div>`;

    document.getElementById("new-playlist").addEventListener("click", openNewPlaylistForm);

    loadSection(document.getElementById("playlists-grid"), () => api("GET", "/api/playlists"), (container, playlists) => {
        if (playlists.length === 0) {
            container.innerHTML = emptyCard("No playlists yet.");
            return;
        }
        const cards = playlists.map((playlist) => `
            <a class="card" href="#/playlists/${playlist.id}">
                <div class="cover" style="background:${colorFor(playlist.name + playlist.id)}">${PLAYLIST_EMOJI[playlist.id % PLAYLIST_EMOJI.length]}</div>
                <div class="card-title">${escapeHtml(playlist.name)}</div>
                <div class="card-sub">by ${escapeHtml(playlist.owner)} · ${playlist.song_count} songs</div>
            </a>`).join("");
        container.innerHTML = `<div class="card-grid">${cards}</div>`;
    });
}

function openNewPlaylistForm() {
    openForm({
        title: "New playlist",
        submitLabel: "Create",
        fields: [{ name: "name", label: "Name" }],
        onSubmit: async (values) => {
            const result = await api("POST", "/api/playlists", { user_id: currentUserId, name: values.name });
            toast(`Created "${values.name}"`);
            location.hash = `#/playlists/${result.new_id}`;
        },
    });
}

async function renderPlaylistPage(playlistId) {
    page.innerHTML = `
        <a class="back-link" href="#/playlists">← All playlists</a>
        <div class="page-header">
            <div>
                <div class="eyebrow">Playlist</div>
                <h1 id="playlist-name">Playlist #${playlistId}</h1>
                <div class="subtitle" id="playlist-subtitle"></div>
            </div>
            <div class="header-actions">
                <button class="button" id="rename-playlist">Rename</button>
                <button class="button danger" id="delete-playlist">Delete</button>
            </div>
        </div>
        <div id="playlist-songs"></div>`;

    // The name comes from list_playlists(). If that isn't written yet, we just show the id.
    let playlistName = `Playlist #${playlistId}`;
    try {
        const playlists = await api("GET", "/api/playlists");
        const playlist = playlists.find((item) => item.id === playlistId);
        if (playlist) {
            playlistName = playlist.name;
            document.getElementById("playlist-name").textContent = playlist.name;
            document.getElementById("playlist-subtitle").textContent = `by ${playlist.owner}`;
        }
    } catch (error) {
        document.getElementById("playlist-subtitle").textContent =
            "(write list_playlists() to see the name and owner)";
    }

    document.getElementById("rename-playlist").addEventListener("click", () => {
        openForm({
            title: "Rename playlist",
            fields: [{ name: "name", label: "Name", value: playlistName }],
            onSubmit: async (values) => {
                await api("PATCH", `/api/playlists/${playlistId}`, { name: values.name });
                toast("Playlist renamed");
                renderCurrentRoute();
            },
        });
    });

    document.getElementById("delete-playlist").addEventListener("click", () => {
        openForm({
            title: "Delete playlist?",
            intro: `Delete <b>${escapeHtml(playlistName)}</b>? The songs stay in your library.`,
            submitLabel: "Delete",
            danger: true,
            onSubmit: async () => {
                await api("DELETE", `/api/playlists/${playlistId}`);
                toast("Playlist deleted");
                location.hash = "#/playlists";
            },
        });
    });

    const songsContainer = document.getElementById("playlist-songs");
    songsContainer.addEventListener("click", (event) => {
        const button = event.target.closest("[data-action=remove]");
        if (!button) return;
        runAction(() => api("DELETE", `/api/playlists/${playlistId}/songs/${button.dataset.id}`), "Removed from playlist");
    });

    loadSection(songsContainer, () => api("GET", `/api/playlists/${playlistId}/songs`), (container, songs) => {
        if (songs.length === 0) {
            container.innerHTML = emptyCard("This playlist is empty. Add songs with the ＋ button on the Songs page.");
            return;
        }
        const totalSeconds = songs.reduce((sum, song) => sum + song.duration_sec, 0);
        const columns = [
            { label: "#", className: "rank", value: (song, index) => index + 1 },
            { label: "Title", className: "title", value: (song) => escapeHtml(song.title) },
            { label: "Artist", value: (song) => escapeHtml(song.artist) },
            { label: "Added", value: (song) => escapeHtml(String(song.added_at).slice(0, 10)) },
            { label: "Time", className: "number", value: (song) => formatDuration(song.duration_sec) },
        ];
        const actions = (song) =>
            `<button class="icon-button delete" data-action="remove" data-id="${song.id}" title="Remove from playlist">✕</button>`;
        container.innerHTML = tableHtml(columns, songs, actions) +
            `<div class="table-footer">${songs.length} songs · ${formatDuration(totalSeconds)}</div>`;
    });
}


// =====================================================================
// CHARTS PAGE
// =====================================================================

function barHtml(value, maxValue) {
    const percent = maxValue > 0 ? Math.round((value / maxValue) * 100) : 0;
    return `<div class="bar" style="width:${percent}%"></div>`;
}

function renderChartsPage() {
    page.innerHTML = `
        <div class="page-header">
            <div><h1>Charts</h1><div class="subtitle">What everyone's listening to</div></div>
        </div>

        <h2>Top songs
            <span class="controls">Show
                <select id="top-limit" class="compact"><option>10</option><option>25</option><option>50</option></select>
            </span>
        </h2>
        <div id="top-songs"></div>

        <h2>#1 song in every genre</h2>
        <div id="genre-leaders"></div>

        <h2>Genres</h2>
        <div id="genre-stats"></div>

        <h2>Most prolific artists
            <span class="controls">at least
                <input id="min-songs" class="compact" type="number" value="20" min="1" style="width:70px"> songs
            </span>
        </h2>
        <div id="prolific-artists"></div>`;

    function loadTopSongs() {
        const limit = document.getElementById("top-limit").value;
        loadSection(document.getElementById("top-songs"), () => api("GET", `/api/charts/top-songs?limit=${limit}`), (container, songs) => {
            const maxPlays = songs.length ? songs[0].play_count : 0;
            container.innerHTML = tableHtml([
                { label: "#", className: "rank", value: (song, index) => index + 1 },
                { label: "Title", className: "title", value: (song) => escapeHtml(song.title) },
                { label: "Artist", value: (song) => escapeHtml(song.artist) },
                { label: "", className: "bar-cell", value: (song) => barHtml(song.play_count, maxPlays) },
                { label: "Plays", className: "number", value: (song) => song.play_count },
            ], songs);
        });
    }

    function loadProlificArtists() {
        const minSongs = document.getElementById("min-songs").value || 1;
        loadSection(document.getElementById("prolific-artists"), () => api("GET", `/api/charts/prolific-artists?min_songs=${minSongs}`), (container, artists) => {
            if (artists.length === 0) {
                container.innerHTML = emptyCard("No artists have that many songs.");
                return;
            }
            const maxSongs = artists[0].song_count;
            container.innerHTML = tableHtml([
                { label: "Artist", className: "title", value: (row) => `<a class="link" href="#/artists/${row.id}">${escapeHtml(row.artist)}</a>` },
                { label: "", className: "bar-cell", value: (row) => barHtml(row.song_count, maxSongs) },
                { label: "Songs", className: "number", value: (row) => row.song_count },
            ], artists);
        });
    }

    document.getElementById("top-limit").addEventListener("change", loadTopSongs);
    document.getElementById("min-songs").addEventListener("change", loadProlificArtists);
    loadTopSongs();
    loadProlificArtists();

    loadSection(document.getElementById("genre-leaders"), () => api("GET", "/api/charts/genre-leaders"), (container, rows) => {
        container.innerHTML = tableHtml([
            { label: "Genre", value: (row) => `<span class="genre-tag">${escapeHtml(row.genre)}</span>` },
            { label: "Song", className: "title", value: (row) => escapeHtml(row.title) },
            { label: "Plays", className: "number", value: (row) => row.play_count },
        ], rows);
    });

    loadSection(document.getElementById("genre-stats"), () => api("GET", "/api/charts/genres"), (container, rows) => {
        const maxCount = rows.length ? Math.max(...rows.map((row) => row.song_count)) : 0;
        container.innerHTML = tableHtml([
            { label: "Genre", value: (row) => `<span class="genre-tag">${escapeHtml(row.genre)}</span>` },
            { label: "", className: "bar-cell", value: (row) => barHtml(row.song_count, maxCount) },
            { label: "Songs", className: "number", value: (row) => row.song_count },
            { label: "Avg length", className: "number", value: (row) => formatDuration(row.avg_duration) },
        ], rows);
    });
}


// =====================================================================
// USERS PAGE
// =====================================================================

function renderUsersPage() {
    page.innerHTML = `
        <div class="page-header"><div><h1>Users</h1></div></div>
        <div id="all-users"></div>
        <h2>Inactive users <span class="controls">never played a song</span></h2>
        <div id="inactive-users"></div>`;

    const userColumns = [
        { label: "Username", className: "title", value: (user) => escapeHtml(user.username) },
        { label: "Country", value: (user) => escapeHtml(user.country) },
        { label: "Joined", value: (user) => escapeHtml(user.joined_date) },
    ];

    loadSection(document.getElementById("all-users"), () => api("GET", "/api/users"), (container, users) => {
        container.innerHTML = tableHtml(userColumns, users) + `<div class="table-footer">${users.length} users</div>`;
    });
    loadSection(document.getElementById("inactive-users"), () => api("GET", "/api/users/inactive"), (container, users) => {
        container.innerHTML = users.length ? tableHtml(userColumns, users) : emptyCard("Everyone has played something!");
    });
}


// =====================================================================
// DATABASE PAGE (developer tools)
// =====================================================================

function renderDatabasePage() {
    page.innerHTML = `
        <div class="page-header">
            <div>
                <h1>Database</h1>
                <div class="subtitle">🔑 = primary key · <span style="color:var(--blue)">→ table.column</span> = foreign key (what you JOIN on). Full details in <code>schema.sql</code>.</div>
            </div>
            <div class="header-actions"><button class="button danger" id="reset-db">Reset database</button></div>
        </div>
        <div id="schema"></div>`;

    document.getElementById("reset-db").addEventListener("click", () => {
        openForm({
            title: "Reset database?",
            intro: "Everything goes back to the original data. Anything you created, edited or deleted is undone.",
            submitLabel: "Reset",
            danger: true,
            onSubmit: async () => {
                await fetch("/api/dev/reset", { method: "POST" });
                toast("Database reset");
                renderCurrentRoute();
            },
        });
    });

    loadSection(document.getElementById("schema"), async () => (await fetch("/api/dev/schema")).json(), (container, tables) => {
        const cards = tables.map((table) => {
            const columns = table.columns.map((column) => {
                const right = column.references
                    ? `<span class="fk">→ ${escapeHtml(column.references)}</span>`
                    : `<span class="type">${escapeHtml(column.type)}</span>`;
                return `<li><span>${column.pk ? "🔑 " : ""}${escapeHtml(column.name)}</span>${right}</li>`;
            }).join("");
            return `
                <div class="schema-card">
                    <h3>${escapeHtml(table.name)} <span>${table.row_count} rows</span></h3>
                    <ul>${columns}</ul>
                </div>`;
        }).join("");
        container.innerHTML = `<div class="schema-grid">${cards}</div>`;
    });
}


// =====================================================================
// FREE PLAY PAGE (developer tools): run SELECTs against the database
// =====================================================================

function renderFreePlayPage() {
    page.innerHTML = `
        <div class="page-header">
            <div>
                <h1>Free play</h1>
                <div class="subtitle">Run any <code>SELECT</code> to explore the tables. Read-only: nothing here can change your data. Press Ctrl/Cmd+Enter to run.</div>
            </div>
        </div>
        <textarea id="freeplay-sql" class="sql-editor" spellcheck="false" rows="6">SELECT * FROM songs LIMIT 10;</textarea>
        <div class="freeplay-actions">
            <button class="button primary" id="freeplay-run">Run query</button>
            <span id="freeplay-meta" class="subtitle"></span>
        </div>
        <div id="freeplay-result"></div>`;

    const editor = document.getElementById("freeplay-sql");
    const result = document.getElementById("freeplay-result");
    const meta = document.getElementById("freeplay-meta");

    async function run() {
        meta.textContent = "Running...";
        const response = await fetch("/api/dev/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sql: editor.value }),
        });
        const payload = await response.json();
        if (!response.ok) {
            meta.textContent = "";
            result.innerHTML = `<pre class="sql-error">${escapeHtml(payload.error)}</pre>`;
            return;
        }
        meta.textContent = `${payload.rows.length} rows · ${payload.ms}ms` +
            (payload.truncated ? ` (showing first ${payload.limit})` : "");
        if (!payload.columns.length) {
            result.innerHTML = emptyCard("No columns returned.");
        } else if (!payload.rows.length) {
            result.innerHTML = emptyCard("Query ran, but returned no rows.");
        } else {
            const columns = payload.columns.map((label, i) => ({
                label,
                value: (row) => row[i] === null ? `<span class="type">NULL</span>` : escapeHtml(String(row[i])),
            }));
            result.innerHTML = tableHtml(columns, payload.rows);
        }
    }

    document.getElementById("freeplay-run").addEventListener("click", run);
    editor.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") run();
    });
    run();
}


// =====================================================================
// SQL LOG DRAWER
// =====================================================================

let logCount = 0;

function addLogEntry(method, path, status, payload) {
    logCount += 1;
    document.getElementById("log-count").textContent = logCount;

    let statusClass = "ok";
    if (payload.error === "not_implemented") statusClass = "todo";
    else if (status >= 400) statusClass = "error";

    let meta = "";
    if (Array.isArray(payload.data)) meta = `${payload.data.length} rows`;
    else if (payload.data && payload.data.rows_affected !== undefined) meta = `${payload.data.rows_affected} changed`;
    if (payload.ms !== undefined) meta += ` · ${payload.ms}ms`;
    if (statusClass === "todo") meta = "not written";

    const details = payload.sql || payload.message || "";
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });

    const entry = document.createElement("details");
    entry.className = "log-entry";
    entry.innerHTML = `
        <summary>
            <span class="log-time">${time}</span>
            <span class="method ${method}">${method}</span>
            <span class="log-status ${statusClass}">${status}</span>
            <span class="log-function">${escapeHtml(payload.function || "")}</span>
            <span>${escapeHtml(path)}</span>
            <span class="log-meta">${escapeHtml(meta)}</span>
        </summary>
        <pre>${escapeHtml(details)}</pre>`;

    const entries = document.getElementById("sql-log-entries");
    entries.prepend(entry);
    while (entries.children.length > 200) {
        entries.lastChild.remove();
    }
}


// =====================================================================
// "Signed in as" picker (needs list_users)
// =====================================================================

async function loadUserPicker() {
    const select = document.getElementById("current-user");
    try {
        const users = await api("GET", "/api/users");
        select.innerHTML = users.map((user) => {
            const selected = user.id === currentUserId ? "selected" : "";
            return `<option value="${user.id}" ${selected}>${escapeHtml(user.username)}</option>`;
        }).join("");
        if (!users.some((user) => user.id === currentUserId) && users.length > 0) {
            currentUserId = users[0].id;
        }
    } catch (error) {
        select.innerHTML = `<option value="${currentUserId}">user #${currentUserId} (write list_users() to switch)</option>`;
        select.disabled = true;
    }
}


// =====================================================================
// Start the app
// =====================================================================

document.getElementById("current-user").addEventListener("change", (event) => {
    currentUserId = Number(event.target.value);
    writeStorage("tunes-user", currentUserId);
    toast(`Signed in as ${event.target.selectedOptions[0].textContent}`);
});
document.getElementById("toggle-log").addEventListener("click", () => {
    document.getElementById("sql-log").classList.toggle("hidden");
});
document.getElementById("close-log").addEventListener("click", () => {
    document.getElementById("sql-log").classList.add("hidden");
});
document.getElementById("clear-log").addEventListener("click", () => {
    document.getElementById("sql-log-entries").innerHTML = "";
    logCount = 0;
    document.getElementById("log-count").textContent = 0;
});
window.addEventListener("hashchange", renderCurrentRoute);

loadUserPicker();
renderCurrentRoute();
