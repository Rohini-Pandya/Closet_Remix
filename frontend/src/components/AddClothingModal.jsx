
import { useEffect, useRef, useState } from "react";
import { Camera, Image as ImageIcon, Info } from "lucide-react";
import Modal from "./ui/Modal";
import {
  CATEGORIES,
  OCCASIONS,
  PATTERNS,
  SEASONS,
  STYLES,
} from "../utils/constants";

const ACCEPT = "image/jpeg,image/png,image/webp";
const MAX_MB = 10;

const INITIAL = {
  item_name: "",
  category: "Tops",
  subcategory: "",
  colour: "",
  colour_hex: "",
  pattern: "Solid",
  style: "Minimal",
  suggested_occasions: ["Casual"],
  season: "All-season",
};

export default function AddClothingModal({ open, onClose, onSave }) {
  const cameraRef = useRef(null);
  const galleryRef = useRef(null);

  const [draft, setDraft] = useState(INITIAL);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) {
      setDraft(INITIAL);
      setPreview(null);
      setError(null);
    }
  }, [open]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const set = (key, value) =>
    setDraft((current) => ({ ...current, [key]: value }));

  const onPick = (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!ACCEPT.split(",").includes(file.type)) {
      setError("Please choose a JPG, PNG or WebP image.");
      return;
    }

    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`That image is larger than ${MAX_MB} MB.`);
      return;
    }

    setError(null);
    setPreview(URL.createObjectURL(file));
  };

  const toggleOccasion = (occasion) => {
    set(
      "suggested_occasions",
      draft.suggested_occasions.includes(occasion)
        ? draft.suggested_occasions.filter((value) => value !== occasion)
        : [...draft.suggested_occasions, occasion]
    );
  };

  const submit = async (e) => {
    e.preventDefault();

    if (!draft.item_name.trim()) {
      setError("Please enter an item name.");
      return;
    }

    setBusy(true);
    setError(null);

    try {
      await onSave({
        ...draft,
        item_name: draft.item_name.trim(),
        subcategory: draft.subcategory.trim() || null,
        colour: draft.colour.trim() || null,
        colour_hex: draft.colour_hex || null,
      });
      onClose();
    } catch (err) {
      setError(err.message || "Couldn't save this clothing item.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add clothing" wide>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">
            Item name *
          </label>
          <input
            className="field mt-1"
            placeholder="e.g. Ivory Ribbed Tee"
            value={draft.item_name}
            onChange={(e) => set("item_name", e.target.value)}
            maxLength={80}
            required
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm">
            Category *
            <select
              className="field mt-1"
              value={draft.category}
              onChange={(e) => set("category", e.target.value)}
            >
              {CATEGORIES.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            Subcategory
            <input
              className="field mt-1"
              placeholder="e.g. T-shirt"
              value={draft.subcategory}
              onChange={(e) => set("subcategory", e.target.value)}
            />
          </label>

          <label className="block text-sm">
            Colour
            <input
              className="field mt-1"
              placeholder="e.g. Ivory"
              value={draft.colour}
              onChange={(e) => set("colour", e.target.value)}
            />
          </label>

          <label className="block text-sm">
            Colour code
            <input
              className="field mt-1"
              type="color"
              value={draft.colour_hex || "#EFEADF"}
              onChange={(e) => set("colour_hex", e.target.value)}
            />
          </label>

          <label className="block text-sm">
            Pattern
            <select
              className="field mt-1"
              value={draft.pattern}
              onChange={(e) => set("pattern", e.target.value)}
            >
              {PATTERNS.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            Style
            <select
              className="field mt-1"
              value={draft.style}
              onChange={(e) => set("style", e.target.value)}
            >
              {STYLES.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>

          <label className="block text-sm sm:col-span-2">
            Season
            <select
              className="field mt-1"
              value={draft.season}
              onChange={(e) => set("season", e.target.value)}
            >
              {SEASONS.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium">Suitable occasions</p>
          <div className="flex flex-wrap gap-2">
            {OCCASIONS.map((occasion) => (
              <label key={occasion} className="chip cursor-pointer">
                <input
                  type="checkbox"
                  className="mr-1.5"
                  checked={draft.suggested_occasions.includes(occasion)}
                  onChange={() => toggleOccasion(occasion)}
                />
                {occasion}
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <input
            ref={cameraRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={onPick}
          />
          <input
            ref={galleryRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={onPick}
          />

          {preview ? (
            <div className="rounded-card border border-line p-3">
              <img
                src={preview}
                alt="Selected clothing"
                className="mx-auto max-h-52 object-contain"
              />
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => cameraRef.current?.click()}
              >
                <Camera className="mr-1 inline h-4 w-4" />
                Take photo
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => galleryRef.current?.click()}
              >
                <ImageIcon className="mr-1 inline h-4 w-4" />
                Choose image
              </button>
            </div>
          )}
        </div>

        <p className="flex items-start gap-2 rounded-lg bg-sage-tint px-3 py-2.5 text-xs text-ink-soft">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          Image upload and AI background removal will be connected in Phase 3.
          For now, the clothing details are saved.
        </p>

        {error && (
          <p role="alert" className="text-sm text-rose-deep">{error}</p>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            className="btn-secondary"
            onClick={onClose}
            disabled={busy}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={busy}
          >
            {busy ? "Saving..." : "Save to wardrobe"}
          </button>
        </div>
      </form>
    </Modal>
  );
}