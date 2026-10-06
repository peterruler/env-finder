'use strict';
const byId = id => document.getElementById(id);
const picker = byId('picker');
let picked = null;
let pickerRequest = 0;

async function loadContents(entries) {
  let next = 0;
  async function worker() {
    while (next < entries.length) {
      const {file, pre, note} = entries[next++];
      try {
        const data = await api('/api/content', {path: file.path});
        pre.textContent = data.content;
        note.textContent = data.warnings.join(' ') || (data.content === '' ? 'Die Datei ist leer.' : '');
      } catch (error) {
        pre.textContent = '';
        note.textContent = `Inhalt konnte nicht geladen werden: ${error.message}`;
      }
    }
  }
  await Promise.all(Array.from({length: Math.min(4, entries.length)}, worker));
}

async function api(endpoint, parameters) {
  const response = await fetch(`${endpoint}?${new URLSearchParams(parameters)}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Die Anfrage ist fehlgeschlagen.');
  return data;
}

async function browse(path) {
  const requestId = ++pickerRequest;
  picked = null;
  byId('select-directory').disabled = true;
  byId('parent').disabled = true;
  byId('folders').replaceChildren();
  byId('picker-status').textContent = 'Ordner werden geladen …';
  try {
    const data = await api('/api/directories', {path});
    if (requestId !== pickerRequest) return;
    picked = data;
    byId('picker-path').textContent = data.display_path;
    byId('select-directory').disabled = false;
    byId('parent').disabled = !data.parent;
    byId('picker-status').textContent = data.directories.length ? `${data.directories.length} Unterordner` : 'Keine Unterordner vorhanden.';
    if (data.skipped) byId('picker-status').textContent += ` ${data.skipped} Einträge konnten nicht gelesen werden.`;
    for (const folder of data.directories) {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'folder';
      button.textContent = `▸  ${folder.name}`;
      button.addEventListener('click', () => browse(folder.path));
      item.append(button);
      byId('folders').append(item);
    }
  } catch (error) {
    if (requestId === pickerRequest) byId('picker-status').textContent = error.message;
  }
}

byId('browse').addEventListener('click', () => { picker.showModal(); browse(byId('directory').value); });
byId('close-picker').addEventListener('click', () => picker.close());
byId('parent').addEventListener('click', () => { if (picked?.parent) browse(picked.parent); });
byId('select-directory').addEventListener('click', () => {
  if (!picked) return;
  byId('directory').value = picked.path;
  byId('selected-path').textContent = picked.display_path;
  picker.close();
});

byId('search-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (byId('search').disabled) return;
  byId('search').disabled = true;
  byId('status').textContent = 'Unterverzeichnisse werden durchsucht …';
  byId('warnings').replaceChildren();
  byId('results-body').replaceChildren();
  byId('results-table').hidden = true;
  byId('count').textContent = '0 Dateien';
  try {
    const data = await api('/api/search', {path: byId('directory').value, variants: byId('variants').checked, bounded: byId('bounded').checked});
    byId('selected-path').textContent = data.directory;
    byId('count').textContent = `${data.count} ${data.count === 1 ? 'Datei' : 'Dateien'}`;
    byId('status').textContent = `${data.truncated ? 'Teilergebnis' : 'Suche abgeschlossen'}: ${data.visited} Ordner in ${data.elapsed.toLocaleString('de-CH')} Sekunden durchsucht.${data.count === 0 ? ' Keine passenden Dateien gefunden.' : ''}`;
    for (const warning of data.warnings) {
      const paragraph = document.createElement('p');
      paragraph.textContent = warning;
      byId('warnings').append(paragraph);
    }
    const contentEntries = [];
    for (const file of data.files) {
      const row = document.createElement('tr');
      const path = document.createElement('td');
      const name = document.createElement('strong');
      name.textContent = file.name;
      const detail = document.createElement('span');
      detail.className = 'file-path';
      detail.textContent = file.path;
      path.append(name, detail);
      const size = document.createElement('td');
      size.textContent = file.size < 1024 ? `${file.size} B` : `${(file.size / 1024).toFixed(1)} KB`;
      const modified = document.createElement('td');
      modified.textContent = new Date(file.modified).toLocaleString('de-CH');
      const action = document.createElement('td');
      const copy = document.createElement('button');
      copy.type = 'button';
      copy.className = 'copy secondary';
      copy.textContent = 'Pfad kopieren';
      copy.setAttribute('aria-label', `Pfad kopieren: ${file.path}`);
      copy.addEventListener('click', async () => {
        try { await navigator.clipboard.writeText(file.path); copy.textContent = 'Kopiert ✓'; }
        catch { byId('status').textContent = 'Kopieren nicht verfügbar. Markiere den angezeigten Pfad und kopiere ihn manuell.'; }
      });
      action.append(copy);
      row.append(path, size, modified, action);
      byId('results-body').append(row);
      const contentRow = document.createElement('tr');
      contentRow.className = 'content-row';
      const cell = document.createElement('td');
      cell.colSpan = 4;
      const details = document.createElement('details');
      details.open = true;
      const summary = document.createElement('summary');
      summary.textContent = 'Dateiinhalt';
      const note = document.createElement('p');
      note.className = 'content-note';
      const pre = document.createElement('pre');
      pre.className = 'env-content';
      pre.setAttribute('aria-label', `Inhalt: ${file.path}`);
      pre.textContent = 'Inhalt wird geladen …';
      details.append(summary, note, pre);
      cell.append(details);
      contentRow.append(cell);
      byId('results-body').append(contentRow);
      contentEntries.push({file, pre, note});
    }
    byId('results-table').hidden = data.count === 0;
    await loadContents(contentEntries);
  } catch (error) { byId('status').textContent = error.message; }
  finally { byId('search').disabled = false; }
});
