// Korean + English OCR with Apple Vision via JXA (osascript) — no compiler or extra packages needed.
// (swiftc on this machine's Command Line Tools fails with "redefinition of module 'SwiftBridging'",
//  and tesseract only has the English model, so this is the Korean-capable OCR path.)
//
// Usage:  osascript -l JavaScript production/qa/vision_ocr.js <image> [<image> ...]
// Output: one JSON line per recognized text: {"file": "...", "text": "...", "conf": 0.98, "box": [x, y, w, h]}
//         box in image pixels, top-left origin.
ObjC.import('Foundation');
ObjC.import('Vision');
ObjC.import('AppKit');

function run(argv) {
  const out = [];
  for (const path of argv) {
    const url = $.NSURL.fileURLWithPath(path);
    const img = $.NSImage.alloc.initWithContentsOfURL(url);
    if (!img || img.isNil()) { out.push(JSON.stringify({ file: path, error: 'cannot open' })); continue; }
    const rep = $.NSBitmapImageRep.imageRepWithData(img.TIFFRepresentation);
    const W = rep.pixelsWide, H = rep.pixelsHigh;
    const handler = $.VNImageRequestHandler.alloc.initWithURLOptions(url, $({}));
    const req = $.VNRecognizeTextRequest.alloc.init;
    req.recognitionLevel = 0;            // VNRequestTextRecognitionLevelAccurate
    req.usesLanguageCorrection = false;
    req.recognitionLanguages = $(['ko-KR', 'en-US']);
    const ok = handler.performRequestsError($([req]), $());
    if (!ok) { out.push(JSON.stringify({ file: path, error: 'ocr failed' })); continue; }
    const res = req.results;
    const n = res.count;
    for (let i = 0; i < n; i++) {
      const obs = res.objectAtIndex(i);
      const cands = obs.topCandidates(1);
      if (!cands.count) continue;
      const c = cands.objectAtIndex(0);
      const b = obs.boundingBox;
      const box = [b.origin.x * W, (1 - b.origin.y - b.size.height) * H, b.size.width * W, b.size.height * H]
        .map((v) => Math.round(v * 10) / 10);
      out.push(JSON.stringify({ file: path, text: ObjC.unwrap(c.string), conf: Math.round(c.confidence * 100) / 100, box }));
    }
  }
  return out.join('\n');
}
