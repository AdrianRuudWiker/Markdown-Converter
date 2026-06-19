"use strict";

// Fully client-side controller. The only network calls are to this same
// local server's /api endpoints — no third-party requests, no CDNs.

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const results = document.getElementById("results");
const acceptedTypesEl = document.getElementById("accepted-types");
const rowTemplate = document.getElementById("result-row-template");

let acceptedExtensions = [];

// Load the supported-formats catalog so we can show accepted types and
// pre-check files before uploading.
async function loadFormats() {
  try {
    const resp = await fetch("/api/formats");
    const formats = await resp.json();
    const enabled = formats.filter((f) => f.implemented).flatMap((f) => f.extensions);
    const planned = formats.filter((f) => !f.implemented).flatMap((f) => f.extensions);
    acceptedExtensions = enabled;
    let text = `Supported now: ${enabled.join(", ") || "none"}.`;
    if (planned.length) text += ` Coming soon: ${planned.join(", ")}.`;
    acceptedTypesEl.textContent = text;
  } catch (err) {
    acceptedTypesEl.textContent = "Could not load supported formats.";
  }
}

function extensionOf(name) {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

// ---- Drag & drop / browse wiring ----------------------------------------

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);

dropzone.addEventListener("drop", (e) => {
  if (e.dataTransfer && e.dataTransfer.files) handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener("change", () => {
  handleFiles(fileInput.files);
  fileInput.value = "";
});

// ---- Conversion ----------------------------------------------------------

function handleFiles(fileList) {
  for (const file of fileList) convertFile(file);
}

function makeRow(filename) {
  const fragment = rowTemplate.content.cloneNode(true);
  const row = fragment.querySelector(".result-row");
  row.querySelector(".result-name").textContent = filename;
  const status = row.querySelector(".result-status");
  status.textContent = "converting...";
  status.className = "result-status converting";
  results.prepend(row);
  return row;
}

async function convertFile(file) {
  const row = makeRow(file.name);
  const status = row.querySelector(".result-status");

  const ext = extensionOf(file.name);
  if (acceptedExtensions.length && !acceptedExtensions.includes(ext)) {
    // Still send it — a planned format yields a friendly server message — but
    // give immediate feedback that it isn't enabled yet.
    status.textContent = "checking...";
  }

  const form = new FormData();
  form.append("file", file);

  try {
    const resp = await fetch("/api/convert", { method: "POST", body: form });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new Error(body.detail || `Conversion failed (${resp.status}).`);
    }
    const data = await resp.json();
    showSuccess(row, data);
  } catch (err) {
    showError(row, err.message);
  }
}

function showSuccess(row, data) {
  const status = row.querySelector(".result-status");
  status.textContent = "done";
  status.className = "result-status ok";

  if (data.warnings && data.warnings.length) {
    const w = row.querySelector(".result-warnings");
    w.hidden = false;
    w.textContent = "Note: " + data.warnings.join(" ");
  }

  const body = row.querySelector(".result-body");
  body.hidden = false;
  const textarea = row.querySelector(".result-markdown");
  textarea.value = data.markdown;

  const baseName = data.filename.replace(/\.[^.]+$/, "") || "document";
  row.querySelector(".download-btn").addEventListener("click", () =>
    downloadMarkdown(baseName + ".md", data.markdown)
  );
  row.querySelector(".copy-btn").addEventListener("click", (e) =>
    copyToClipboard(data.markdown, e.target)
  );
}

function showError(row, message) {
  const status = row.querySelector(".result-status");
  status.textContent = "error";
  status.className = "result-status error";
  const errEl = row.querySelector(".result-error");
  errEl.hidden = false;
  errEl.textContent = message;
}

function downloadMarkdown(filename, markdown) {
  const blob = new Blob([markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function copyToClipboard(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    const original = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => (button.textContent = original), 1500);
  } catch (err) {
    button.textContent = "Copy failed";
  }
}

loadFormats();
