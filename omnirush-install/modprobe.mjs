// 在 Node 中以最小 DOM 桩加载 bundle，验证模块求值阶段是否抛异常
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

function anyStub(name) {
  const f = function () {
    return anyStub(name + "()");
  };
  return new Proxy(f, {
    get(t, p) {
      if (p === "then") return undefined; // 防止被当作 thenable
      if (p === Symbol.toPrimitive) return () => "[stub:" + name + "]";
      if (p === "length") return 0;
      if (p === "nodeType") return 1;
      if (p === "style") return anyStub(name + ".style");
      if (p === "classList") return { add() {}, remove() {}, toggle() {} };
      if (p === "setAttribute") return () => {};
      if (p === "appendChild") return () => anyStub("child");
      if (p === "removeChild") return () => anyStub("child");
      if (p === "addEventListener") return () => {};
      if (p === "removeEventListener") return () => {};
      if (p === "querySelector") return () => null;
      if (p === "querySelectorAll") return () => [];
      if (p === "getContext") return () => null;
      return anyStub(name + "." + String(p));
    },
    apply() {
      return anyStub(name + "()");
    },
    construct() {
      return anyStub("new " + name);
    },
  });
}

const doc = anyStub("document");
function def(name, value) {
  Object.defineProperty(globalThis, name, {
    value,
    configurable: true,
    writable: true,
  });
}
def("document", doc);
def("navigator", anyStub("navigator"));
globalThis.window = anyStub("window");
globalThis.localStorage = anyStub("localStorage");
globalThis.sessionStorage = anyStub("sessionStorage");
globalThis.matchMedia = () => anyStub("matchMedia");
globalThis.location = anyStub("location");
globalThis.history = anyStub("history");
globalThis.getComputedStyle = () => anyStub("computedStyle");
globalThis.requestAnimationFrame = (cb) => setTimeout(cb, 0);
globalThis.cancelAnimationFrame = () => {};
globalThis.CSS = anyStub("CSS");
globalThis.MutationObserver = anyStub("MutationObserver");
globalThis.ResizeObserver = anyStub("ResizeObserver");
globalThis.IntersectionObserver = anyStub("IntersectionObserver");
globalThis.Notification = anyStub("Notification");
globalThis.fetch = () => Promise.reject(new Error("stub fetch"));
globalThis.WebSocket = anyStub("WebSocket");
globalThis.indexedDB = anyStub("indexedDB");
def("crypto", anyStub("crypto"));
globalThis.performance = globalThis.performance || anyStub("performance");
globalThis.CustomEvent = anyStub("CustomEvent");
globalThis.Event = anyStub("Event");
globalThis.Element = anyStub("Element");
globalThis.HTMLElement = anyStub("HTMLElement");
globalThis.Node = anyStub("Node");
globalThis.Worker = anyStub("Worker");

const target = process.argv[2] || "./app-CAtSUbH6.js";
const url = new URL(target, "file://" + HERE + "/").href;

console.log("加载:", url);
const t0 = Date.now();
try {
  await import(url);
  console.log(`✅ 模块求值成功（${Date.now() - t0} ms）—— 顶部没有抛异常`);
} catch (e) {
  console.log(`❌ 模块求值抛出异常（${Date.now() - t0} ms）`);
  console.log("  构造器:", e && e.constructor && e.constructor.name);
  console.log("  消息:", String(e && e.message).slice(0, 3000));
  console.log("  堆栈:");
  console.log(String((e && e.stack) || "").split("\n").slice(0, 25).join("\n"));
  process.exitCode = 2;
}
