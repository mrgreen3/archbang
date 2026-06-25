PAGE_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FruitBang Installer</title>
<style>
  body { background:#201b14; color:#c9c0b0; font-family:monospace;
         max-width:640px; margin:40px auto; padding:0 16px; line-height:1.5; }
  h1, h2 { color:#c9b890; }
  .panel { display:none; }
  .panel.active { display:block; }
  button { background:#c9b890; color:#201b14; border:none; border-radius:6px;
           padding:10px 18px; font-family:monospace; font-size:1em; cursor:pointer; margin-right:8px; }
  button:disabled { opacity:0.4; cursor:default; }
  button.danger { background:#e06060; color:#fff; }
  label { display:block; margin:8px 0; }
  input[type=text], input[type=password] {
    background:#2c261d; color:#c9c0b0; border:1px solid #c9b890;
    border-radius:6px; padding:6px; font-family:monospace; width:100%; box-sizing:border-box; }
  select {
    background:#2c261d; color:#c9c0b0; border:1px solid #c9b890;
    border-radius:6px; padding:6px; font-family:monospace; }
  .warn { color:#e0a060; border:1px solid #e0a060; border-radius:6px; padding:10px; margin-bottom:12px; }
  .err  { color:#e06060; border:1px solid #e06060; border-radius:6px; padding:10px; margin:10px 0; }
  #bar { background:#2c261d; border-radius:6px; height:24px; overflow:hidden; margin:12px 0; }
  #fill { background:#c9b890; height:100%; width:0%; transition:width 0.3s; }
  pre { background:#2c261d; border-radius:6px; padding:8px; font-size:0.85em; white-space:pre-wrap; }
  #steps { display:flex; justify-content:center; margin-bottom:24px; }
  .step { display:flex; flex-direction:column; align-items:center; gap:4px; flex:1; opacity:.35; }
  .step.active { opacity:1; }
  .step-num { background:#2c261d; color:#c9b890; border:2px solid #3a3228; border-radius:50%;
              width:28px; height:28px; line-height:28px; text-align:center; font-size:.85em; }
  .step.active .step-num { background:#c9b890; color:#201b14; border-color:#c9b890; }
  .step.done .step-num { background:#c9b890; color:#201b14; border-color:#c9b890; }
  .step.done { opacity:.7; }
  .step-lbl { font-size:.7em; color:#8c8070; }
  .step.active .step-lbl { color:#c9c0b0; }
  #pct-num { display:block; font-size:3em; font-weight:bold; color:#c9b890;
             text-align:center; line-height:1; margin:12px 0 4px; }
  #step { display:block; text-align:center; color:#8c8070; margin-bottom:12px; font-size:.9em; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }
  #fill.running { animation:pulse 1.5s ease-in-out infinite; }
  #logtail-wrap { background:#0d0b07; border-radius:6px; padding:4px 8px;
                  max-height:200px; overflow-y:auto; margin-top:8px; }
  #logtail-wrap pre { background:transparent; padding:0; margin:0; font-size:.8em; color:#7a9960; }
  .section-lbl { color:#8c8070; font-size:.85em; margin:12px 0 4px; }
  .section-rule { border:none; border-top:1px solid #3a3228; margin:16px 0 4px; }
</style>
</head>
<body>
<div style="text-align:center; margin-bottom:24px;">
  <svg xmlns="http://www.w3.org/2000/svg" width="300" height="120" viewBox="0 0 300 120">
    <rect width="300" height="120" rx="12" fill="#2c261d"/>
    <text x="150" y="70" text-anchor="middle" font-family="monospace" font-size="56"
          font-weight="bold" fill="#c9b890">^!</text>
    <text x="150" y="98" text-anchor="middle" font-family="monospace" font-size="15"
          fill="#c9c0b0" letter-spacing="5">FruitBang</text>
  </svg>
</div>
<div id="steps">
  <div class="step active" id="s-welcome"><div class="step-num">1</div><div class="step-lbl">Welcome</div></div>
  <div class="step" id="s-disk"><div class="step-num">2</div><div class="step-lbl">Disk</div></div>
  <div class="step" id="s-configure"><div class="step-num">3</div><div class="step-lbl">Configure</div></div>
  <div class="step" id="s-install"><div class="step-num">4</div><div class="step-lbl">Install</div></div>
  <div class="step" id="s-done"><div class="step-num">5</div><div class="step-lbl">Done</div></div>
</div>
<div id="err" class="err" style="display:none"></div>

<div id="p-welcome" class="panel active">
  <div class="warn"><b>Warning:</b> Installing will erase the target disk — back up anything first.</div>
  <p>Requirements: booted from FruitBang live ISO, 4GB+ RAM, 20GB+ target disk.</p>
  <div style="text-align:center;"><button onclick="show('mode')">Begin</button></div>
</div>

<div id="p-mode" class="panel">
  <h2>Partitioning</h2>
  <p><b>Auto</b> — wipe a whole disk and partition it automatically.</p>
  <p><b>Custom</b> — wipe a whole disk and define your own partitions.</p>
  <p><b>Manual</b> — you have already partitioned; select existing partitions.</p>
  <div style="display:flex;gap:8px;">
    <button style="flex:1" onclick="showAuto()">Auto</button>
    <button style="flex:1" onclick="showCustom()">Custom</button>
    <button style="flex:1" onclick="showManual()">Manual</button>
  </div>
</div>

<div id="p-autodisk" class="panel">
  <h2>Auto-partition</h2>
  <div class="warn"><b>WARNING: All data on the selected disk will be permanently erased.</b></div>
  <label>Disk: <select id="wholedisk"></select></label>
  <p id="autodisk-uefi"></p>
  <button class="danger" onclick="confirmAutopart()">Erase disk and partition</button>
</div>

<div id="p-custom" class="panel">
  <h2>Custom Layout</h2>
  <div class="warn"><b>WARNING: All data on the selected disk will be permanently erased.</b></div>
  <label>Disk: <select id="customdisk"></select></label>
  <p id="custom-uefi" class="section-lbl"></p>
  <div id="partrows"></div>
  <button onclick="addRow()">+ Add partition</button>
  <hr class="section-rule">
  <button class="danger" onclick="createLayout()">Create layout and format</button>
</div>

<div id="p-disk" class="panel">
  <h2>Select Partitions</h2>
  <p>Choose the root partition (and EFI partition if UEFI).</p>
  <div id="disks">Loading...</div>
  <label>Root partition: <select id="root"></select></label>
  <label>EFI partition (UEFI only, else leave blank):
    <select id="efi"><option value="">none</option></select></label>
  <button onclick="checkPartitions()">Continue</button>
</div>

<div id="p-part" class="panel">
  <h2>Partition the Disk</h2>
  <p>If your disk is not yet partitioned, open a terminal and run:</p>
  <pre>sudo cfdisk /dev/sdX</pre>
  <p>Create a root partition (and a 512M EFI partition for UEFI). Return here when done.</p>
  <button onclick="loadDisks()">Re-scan partitions</button>
</div>

<div id="p-install" class="panel">
  <h2>Installing</h2>
  <span id="pct-num">0%</span>
  <span id="step">Starting…</span>
  <div id="bar"><div id="fill"></div></div>
  <div id="logtail-wrap"><pre id="logtail"></pre></div>
</div>

<div id="p-configure" class="panel">
  <h2>Configure System</h2>
  <p class="section-lbl">System identity</p>
  <label>Hostname: <input type="text" id="hostname" value="fruitbang"></label>
  <label>Username: <input type="text" id="username"></label>
  <label>Password: <input type="password" id="pw1"></label>
  <label>Confirm password: <input type="password" id="pw2"></label>
  <hr class="section-rule">
  <p class="section-lbl">Localisation</p>
  <label>Timezone:
    <select id="timezone">
      <optgroup label="Europe">
        <option value="Europe/London">Europe/London</option>
        <option value="Europe/Dublin">Europe/Dublin</option>
        <option value="Europe/Lisbon">Europe/Lisbon</option>
        <option value="Europe/Paris">Europe/Paris</option>
        <option value="Europe/Brussels">Europe/Brussels</option>
        <option value="Europe/Amsterdam">Europe/Amsterdam</option>
        <option value="Europe/Berlin">Europe/Berlin</option>
        <option value="Europe/Vienna">Europe/Vienna</option>
        <option value="Europe/Zurich">Europe/Zurich</option>
        <option value="Europe/Madrid">Europe/Madrid</option>
        <option value="Europe/Rome">Europe/Rome</option>
        <option value="Europe/Warsaw">Europe/Warsaw</option>
        <option value="Europe/Stockholm">Europe/Stockholm</option>
        <option value="Europe/Oslo">Europe/Oslo</option>
        <option value="Europe/Copenhagen">Europe/Copenhagen</option>
        <option value="Europe/Helsinki">Europe/Helsinki</option>
        <option value="Europe/Athens">Europe/Athens</option>
        <option value="Europe/Bucharest">Europe/Bucharest</option>
        <option value="Europe/Moscow">Europe/Moscow</option>
        <option value="Europe/Istanbul">Europe/Istanbul</option>
      </optgroup>
      <optgroup label="America">
        <option value="America/New_York">America/New_York</option>
        <option value="America/Chicago">America/Chicago</option>
        <option value="America/Denver">America/Denver</option>
        <option value="America/Los_Angeles">America/Los_Angeles</option>
        <option value="America/Toronto">America/Toronto</option>
        <option value="America/Montreal" selected>America/Montreal</option>
        <option value="America/Vancouver">America/Vancouver</option>
        <option value="America/Sao_Paulo">America/Sao_Paulo</option>
        <option value="America/Mexico_City">America/Mexico_City</option>
        <option value="America/Argentina/Buenos_Aires">America/Argentina/Buenos_Aires</option>
      </optgroup>
      <optgroup label="Asia">
        <option value="Asia/Dubai">Asia/Dubai</option>
        <option value="Asia/Kolkata">Asia/Kolkata</option>
        <option value="Asia/Bangkok">Asia/Bangkok</option>
        <option value="Asia/Singapore">Asia/Singapore</option>
        <option value="Asia/Shanghai">Asia/Shanghai</option>
        <option value="Asia/Tokyo">Asia/Tokyo</option>
        <option value="Asia/Seoul">Asia/Seoul</option>
        <option value="Asia/Jerusalem">Asia/Jerusalem</option>
      </optgroup>
      <optgroup label="Africa / Pacific / Other">
        <option value="Africa/Johannesburg">Africa/Johannesburg</option>
        <option value="Africa/Cairo">Africa/Cairo</option>
        <option value="Australia/Sydney">Australia/Sydney</option>
        <option value="Pacific/Auckland">Pacific/Auckland</option>
        <option value="UTC">UTC</option>
      </optgroup>
    </select>
  </label>
  <label>Locale:
    <select id="locale">
      <option value="en_GB.UTF-8">en_GB.UTF-8 (English UK)</option>
      <option value="en_US.UTF-8" selected>en_US.UTF-8 (English US)</option>
      <option value="de_DE.UTF-8">de_DE.UTF-8 (German)</option>
      <option value="fr_FR.UTF-8">fr_FR.UTF-8 (French)</option>
      <option value="es_ES.UTF-8">es_ES.UTF-8 (Spanish)</option>
      <option value="it_IT.UTF-8">it_IT.UTF-8 (Italian)</option>
      <option value="pt_PT.UTF-8">pt_PT.UTF-8 (Portuguese)</option>
      <option value="pt_BR.UTF-8">pt_BR.UTF-8 (Brazilian Portuguese)</option>
      <option value="nl_NL.UTF-8">nl_NL.UTF-8 (Dutch)</option>
      <option value="pl_PL.UTF-8">pl_PL.UTF-8 (Polish)</option>
      <option value="ru_RU.UTF-8">ru_RU.UTF-8 (Russian)</option>
      <option value="sv_SE.UTF-8">sv_SE.UTF-8 (Swedish)</option>
      <option value="nb_NO.UTF-8">nb_NO.UTF-8 (Norwegian)</option>
      <option value="da_DK.UTF-8">da_DK.UTF-8 (Danish)</option>
      <option value="fi_FI.UTF-8">fi_FI.UTF-8 (Finnish)</option>
      <option value="zh_CN.UTF-8">zh_CN.UTF-8 (Chinese Simplified)</option>
      <option value="ja_JP.UTF-8">ja_JP.UTF-8 (Japanese)</option>
      <option value="ko_KR.UTF-8">ko_KR.UTF-8 (Korean)</option>
    </select>
  </label>
  <label>Keyboard layout:
    <select id="keymap">
      <option value="us" selected>US English</option>
      <option value="gb">UK English</option>
      <option value="de">German</option>
      <option value="fr">French</option>
      <option value="es">Spanish</option>
      <option value="it">Italian</option>
      <option value="pt">Portuguese</option>
      <option value="br">Brazilian Portuguese</option>
      <option value="nl">Dutch</option>
      <option value="pl">Polish</option>
      <option value="ru">Russian</option>
      <option value="se">Swedish</option>
      <option value="no">Norwegian</option>
      <option value="dk">Danish</option>
      <option value="fi">Finnish</option>
      <option value="be">Belgian</option>
      <option value="ch">Swiss</option>
    </select>
  </label>
  <button onclick="startInstall()">Install</button>
</div>

<div id="p-done" class="panel">
  <h2>Installation Complete</h2>
  <p>Remove the ISO and reboot into your new system.</p>
  <button onclick="doReboot()">Reboot</button>
  <h2>Post-install checklist</h2>
  <p><b>1. Networking</b><br>
  Click the network icon in the panel.</p>
  <p><b>2. Pacman keyring</b><br>
  Run <code>~/Scripts/fix-keys</code> to initialise and populate the keyring before installing anything.</p>
  <p><b>3. Update mirrors</b><br>
  Run <code>sudo reflector --country GB --latest 10 --sort rate --save /etc/pacman.d/mirrorlist</code> (adjust country code as needed).</p>
  <p><b>4. Install yay (AUR helper)</b><br>
  Required to build MangoWM and AUR packages:<br>
  <code>sudo pacman -S --needed git base-devel<br>
git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si</code></p>
</div>

<script>
const sel = {};  // chosen partitions carried through panels
const STEP_MAP = {
  welcome:'welcome', mode:'disk', autodisk:'disk', custom:'disk',
  disk:'disk', part:'disk', configure:'configure',
  install:'install', done:'done'
};
const STEP_ORDER = ['welcome','disk','configure','install','done'];
function show(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('p-' + name).classList.add('active');
  const step = STEP_MAP[name];
  const activeIdx = STEP_ORDER.indexOf(step);
  document.querySelectorAll('.step').forEach((el, i) => {
    el.classList.remove('active','done');
    if (i < activeIdx) el.classList.add('done');
    else if (i === activeIdx) el.classList.add('active');
  });
}
function showErr(msg) {
  const e = document.getElementById('err');
  e.textContent = msg; e.style.display = msg ? 'block' : 'none';
}
async function showAuto() {
  showErr('');
  const r = await fetch('/api/whole_disks'); const d = await r.json();
  const s = document.getElementById('wholedisk');
  s.innerHTML = '';
  if (!d.disks.length) { showErr('No disks found'); return; }
  d.disks.forEach(p => s.add(new Option(p.path + ' (' + p.size + ')', p.path)));
  document.getElementById('autodisk-uefi').textContent =
    d.uefi ? 'UEFI mode: will create 512M EFI + root partitions (GPT).'
           : 'BIOS mode: will create single root partition (MBR).';
  show('autodisk');
}
async function confirmAutopart() {
  showErr('');
  const disk = document.getElementById('wholedisk').value;
  if (!disk) return showErr('No disk selected');
  const btn = document.querySelector('#p-autodisk .danger');
  btn.disabled = true; btn.textContent = 'Partitioning…';
  const r = await fetch('/api/autopart', {method:'POST', body: JSON.stringify({disk})});
  const d = await r.json();
  btn.disabled = false; btn.textContent = 'Erase disk and partition';
  if (!d.ok) return showErr(d.error);
  sel.root_part = d.root_part;
  sel.efi_part = d.efi_part || '';
  show('configure');
}
let customUefi = false;
let rows = [];  // [{size, role, fs}] in on-disk order
async function showCustom() {
  showErr('');
  let d;
  try {
    const r = await fetch('/api/whole_disks'); d = await r.json();
  } catch (e) { return showErr('Could not query disks: ' + e); }
  if (!d || !d.ok) return showErr((d && d.error) || 'Could not query disks');
  const s = document.getElementById('customdisk'); s.innerHTML = '';
  if (!d.disks.length) { showErr('No disks found'); return; }
  d.disks.forEach(p => s.add(new Option(p.path + ' (' + p.size + ')', p.path)));
  customUefi = !!d.uefi;
  document.getElementById('custom-uefi').textContent = customUefi
    ? 'UEFI (GPT): include exactly one EFI partition.'
    : 'BIOS (MBR): no EFI partition, max 4 partitions.';
  rows = customUefi
    ? [{size:'512M', role:'efi', fs:'ext4'}, {size:'', role:'root', fs:'ext4'}]
    : [{size:'', role:'root', fs:'ext4'}];
  renderRows();
  show('custom');
}
function renderRows() {
  const c = document.getElementById('partrows');
  c.innerHTML = '';
  rows.forEach((row, i) => {
    const div = document.createElement('div');
    div.style.cssText = 'display:flex; gap:6px; align-items:center; margin:6px 0; flex-wrap:wrap;';

    const size = document.createElement('input');
    size.type = 'text'; size.style.width = '90px';
    size.placeholder = 'size'; size.value = row.size;
    size.addEventListener('input', () => { rows[i].size = size.value; });

    const roleSel = document.createElement('select');
    (customUefi ? ['root','efi','swap','home'] : ['root','swap','home'])
      .forEach(r => roleSel.add(new Option(r, r)));
    roleSel.value = row.role;
    roleSel.addEventListener('change', () => { rows[i].role = roleSel.value; renderRows(); });

    div.appendChild(size);
    div.appendChild(roleSel);

    if (row.role === 'root' || row.role === 'home') {
      const fsSel = document.createElement('select');
      ['ext4','btrfs','xfs'].forEach(f => fsSel.add(new Option(f, f)));
      fsSel.value = row.fs;
      fsSel.addEventListener('change', () => { rows[i].fs = fsSel.value; });
      div.appendChild(fsSel);
    }

    const del = document.createElement('button');
    del.textContent = 'x'; del.disabled = rows.length <= 1;
    del.addEventListener('click', () => { rows.splice(i, 1); renderRows(); });
    div.appendChild(del);

    c.appendChild(div);
  });
  const hint = document.createElement('div');
  hint.className = 'section-lbl';
  hint.textContent = 'Leave the last size blank to use remaining space. Sizes e.g. 512M, 30G.';
  c.appendChild(hint);
}
function addRow() { rows.push({size:'10G', role:'home', fs:'ext4'}); renderRows(); }
async function createLayout() {
  showErr('');
  const disk = document.getElementById('customdisk').value;
  if (!disk) return showErr('No disk selected');
  const btn = document.querySelector('#p-custom .danger');
  btn.disabled = true; btn.textContent = 'Creating…';
  let d;
  try {
    const r = await fetch('/api/custompart', {method:'POST', body: JSON.stringify({disk, parts: rows})});
    d = await r.json();
  } catch (e) {
    btn.disabled = false; btn.textContent = 'Create layout and format';
    return showErr('Request failed: ' + e);
  }
  btn.disabled = false; btn.textContent = 'Create layout and format';
  if (!d.ok) return showErr(d.error);
  sel.root_part = d.root_part;
  sel.efi_part = d.efi_part || '';
  sel.swap_part = d.swap_part || '';
  sel.home_part = d.home_part || '';
  show('configure');
}
async function showManual() {
  showErr('');
  await loadDisks();
}
async function loadDisks() {
  showErr('');
  let d;
  try {
    const r = await fetch('/api/disks'); d = await r.json();
  } catch (e) { return showErr('Could not query partitions: ' + e); }
  if (!d || !d.ok) return showErr((d && d.error) || 'Could not query partitions');
  const root = document.getElementById('root'), efi = document.getElementById('efi');
  // Rebuild from scratch so re-entry doesn't duplicate options.
  root.innerHTML = '';
  efi.innerHTML = '<option value="">none</option>';
  const parts = d.disks || [];
  if (!parts.length) {
    // Nothing to select — send the user to the partitioning instructions
    // instead of stranding them on an empty dropdown.
    show('part');
    return;
  }
  document.getElementById('disks').textContent =
    parts.map(p => p.path + ' (' + p.size + ')').join(', ');
  parts.forEach(p => {
    root.add(new Option(p.path + ' (' + p.size + ')', p.path));
    efi.add(new Option(p.path + ' (' + p.size + ')', p.path));
  });
  show('disk');
}
async function checkPartitions() {
  showErr('');
  sel.root_part = document.getElementById('root').value;
  sel.efi_part = document.getElementById('efi').value;
  const r = await fetch('/api/partition', {method:'POST',
    body: JSON.stringify(sel)});
  const d = await r.json();
  if (!d.ok) return showErr(d.error);
  show('configure');
}
let _maxPct = 0;
async function startInstall() {
  showErr('');
  const pw1 = document.getElementById('pw1').value;
  if (pw1 !== document.getElementById('pw2').value) return showErr('Passwords do not match');
  const cfg = Object.assign({}, sel, {
    hostname: document.getElementById('hostname').value,
    username: document.getElementById('username').value,
    password: pw1,
    timezone: document.getElementById('timezone').value,
    locale: document.getElementById('locale').value,
    keymap: document.getElementById('keymap').value,
  });
  const r = await fetch('/api/install', {method:'POST', body: JSON.stringify(cfg)});
  const d = await r.json();
  if (!d.ok) return showErr(d.error);
  _maxPct = 0;
  show('install');
  document.getElementById('fill').classList.add('running');
  poll();
}
async function poll() {
  const r = await fetch('/api/progress'); const s = await r.json();
  if (s.percent > _maxPct) _maxPct = s.percent;
  document.getElementById('fill').style.width = _maxPct + '%';
  document.getElementById('pct-num').textContent = _maxPct + '%';
  document.getElementById('step').textContent = s.step || '';
  if (s.error) { showErr(s.error); return; }
  if (s.done) { document.getElementById('fill').classList.remove('running'); show('done'); return; }
  setTimeout(poll, 2000);
}
async function doReboot() { await fetch('/api/reboot', {method:'POST', body:'{}'}); }
</script>
<footer style="text-align:center; margin-top:40px; font-size:0.8em; color:#6b6050;">
  &copy; 2026 FruitBang &mdash; MIT Licence
</footer>
</body>
</html>"""
