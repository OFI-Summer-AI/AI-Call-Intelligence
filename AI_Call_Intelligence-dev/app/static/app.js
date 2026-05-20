// Update boot message now that Babel is running
(function () {
  var m = document.getElementById('boot-msg');
  if (m) m.textContent = 'Starting…';
})();
const {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo
} = React;
const {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  CartesianGrid
} = Recharts;

// ── SVG Icon primitives ────────────────────────────────────────────────────
const Svg = ({
  s = 16,
  c = "",
  children
}) => /*#__PURE__*/React.createElement("svg", {
  width: s,
  height: s,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  className: c
}, children);
const IcoHome = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
}), /*#__PURE__*/React.createElement("polyline", {
  points: "9 22 9 12 15 12 15 22"
}));
const IcoFiles = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
}), /*#__PURE__*/React.createElement("polyline", {
  points: "14 2 14 8 20 8"
}), /*#__PURE__*/React.createElement("line", {
  x1: "16",
  y1: "13",
  x2: "8",
  y2: "13"
}), /*#__PURE__*/React.createElement("line", {
  x1: "16",
  y1: "17",
  x2: "8",
  y2: "17"
}), /*#__PURE__*/React.createElement("line", {
  x1: "10",
  y1: "9",
  x2: "8",
  y2: "9"
}));
const IcoLive = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("polyline", {
  points: "22 12 18 12 15 21 9 3 6 12 2 12"
}));
const IcoCal = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("rect", {
  x: "3",
  y: "4",
  width: "18",
  height: "18",
  rx: "2",
  ry: "2"
}), /*#__PURE__*/React.createElement("line", {
  x1: "16",
  y1: "2",
  x2: "16",
  y2: "6"
}), /*#__PURE__*/React.createElement("line", {
  x1: "8",
  y1: "2",
  x2: "8",
  y2: "6"
}), /*#__PURE__*/React.createElement("line", {
  x1: "3",
  y1: "10",
  x2: "21",
  y2: "10"
}));
const IcoReq = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("line", {
  x1: "8",
  y1: "6",
  x2: "21",
  y2: "6"
}), /*#__PURE__*/React.createElement("line", {
  x1: "8",
  y1: "12",
  x2: "21",
  y2: "12"
}), /*#__PURE__*/React.createElement("line", {
  x1: "8",
  y1: "18",
  x2: "21",
  y2: "18"
}), /*#__PURE__*/React.createElement("line", {
  x1: "3",
  y1: "6",
  x2: "3.01",
  y2: "6"
}), /*#__PURE__*/React.createElement("line", {
  x1: "3",
  y1: "12",
  x2: "3.01",
  y2: "12"
}), /*#__PURE__*/React.createElement("line", {
  x1: "3",
  y1: "18",
  x2: "3.01",
  y2: "18"
}));
const IcoBack = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("line", {
  x1: "19",
  y1: "12",
  x2: "5",
  y2: "12"
}), /*#__PURE__*/React.createElement("polyline", {
  points: "12 19 5 12 12 5"
}));
const IcoDl = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
}), /*#__PURE__*/React.createElement("polyline", {
  points: "7 10 12 15 17 10"
}), /*#__PURE__*/React.createElement("line", {
  x1: "12",
  y1: "15",
  x2: "12",
  y2: "3"
}));
const IcoRefresh = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("polyline", {
  points: "23 4 23 10 17 10"
}), /*#__PURE__*/React.createElement("polyline", {
  points: "1 20 1 14 7 14"
}), /*#__PURE__*/React.createElement("path", {
  d: "M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"
}));
const IcoUpload = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
}), /*#__PURE__*/React.createElement("polyline", {
  points: "17 8 12 3 7 8"
}), /*#__PURE__*/React.createElement("line", {
  x1: "12",
  y1: "3",
  x2: "12",
  y2: "15"
}));
const IcoSearch = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("circle", {
  cx: "11",
  cy: "11",
  r: "8"
}), /*#__PURE__*/React.createElement("line", {
  x1: "21",
  y1: "21",
  x2: "16.65",
  y2: "16.65"
}));
const IcoCheck = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("polyline", {
  points: "20 6 9 17 4 12"
}));
const IcoAlert = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
}), /*#__PURE__*/React.createElement("line", {
  x1: "12",
  y1: "9",
  x2: "12",
  y2: "13"
}), /*#__PURE__*/React.createElement("line", {
  x1: "12",
  y1: "17",
  x2: "12.01",
  y2: "17"
}));
const IcoShield = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
}));
const IcoUser = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"
}), /*#__PURE__*/React.createElement("circle", {
  cx: "12",
  cy: "7",
  r: "4"
}));
const IcoClock = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("circle", {
  cx: "12",
  cy: "12",
  r: "10"
}), /*#__PURE__*/React.createElement("polyline", {
  points: "12 6 12 12 16 14"
}));
const IcoChevD = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("polyline", {
  points: "6 9 12 15 18 9"
}));
const IcoChevR = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("polyline", {
  points: "9 18 15 12 9 6"
}));
const IcoX = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("circle", {
  cx: "12",
  cy: "12",
  r: "10"
}), /*#__PURE__*/React.createElement("line", {
  x1: "15",
  y1: "9",
  x2: "9",
  y2: "15"
}), /*#__PURE__*/React.createElement("line", {
  x1: "9",
  y1: "9",
  x2: "15",
  y2: "15"
}));
const IcoLink = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("path", {
  d: "M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"
}), /*#__PURE__*/React.createElement("path", {
  d: "M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"
}));
const IcoSpin = ({
  s = 16,
  c = ""
}) => /*#__PURE__*/React.createElement("svg", {
  width: s,
  height: s,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: "2",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  className: "spin " + c
}, /*#__PURE__*/React.createElement("path", {
  d: "M21 12a9 9 0 1 1-6.219-8.56"
}));
const IcoMenu = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("line", {
  x1: "3",
  y1: "12",
  x2: "21",
  y2: "12"
}), /*#__PURE__*/React.createElement("line", {
  x1: "3",
  y1: "6",
  x2: "21",
  y2: "6"
}), /*#__PURE__*/React.createElement("line", {
  x1: "3",
  y1: "18",
  x2: "21",
  y2: "18"
}));
const IcoPanelLeft = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("rect", {
  x: "3",
  y: "3",
  width: "18",
  height: "18",
  rx: "2"
}), /*#__PURE__*/React.createElement("line", {
  x1: "9",
  y1: "3",
  x2: "9",
  y2: "21"
}));
const IcoPanelRight = p => /*#__PURE__*/React.createElement(Svg, p, /*#__PURE__*/React.createElement("rect", {
  x: "3",
  y: "3",
  width: "18",
  height: "18",
  rx: "2"
}), /*#__PURE__*/React.createElement("line", {
  x1: "15",
  y1: "3",
  x2: "15",
  y2: "21"
}));

// ── Utilities ──────────────────────────────────────────────────────────────
const API = typeof window.__API_BASE__ !== 'undefined' && window.__API_BASE__ && !window.__API_BASE__.startsWith('__') ? window.__API_BASE__ : 'http://localhost:8000';
const prettify = id => {
  const n = id.replace(/_\d{4}-\d{2}-\d{2}T[\d-]+$/, '');
  return (n.replace(/_/g, ' ').replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || id).trim();
};
const parseDate = id => {
  const m = id.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})/);
  if (!m) return '';
  const [, y, mo, d, h, mi] = m;
  return new Date(+y, +mo - 1, +d, +h, +mi).toLocaleString('en', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
const getDuration = t => {
  if (!t?.length) return '-';
  const p = (t[t.length - 1].end || '00:00:00').split(':');
  try {
    const m = +p[0] * 60 + +p[1];
    return m ? `${m} min` : '<1 min';
  } catch {
    return '-';
  }
};
const countMinutes = recs => recs.reduce((s, r) => {
  const t = r.transcript || [];
  if (!t.length) return s;
  const p = (t[t.length - 1].end || '0:0').split(':');
  try {
    return s + +p[0] * 60 + +p[1];
  } catch {
    return s;
  }
}, 0);
const confColor = v => v == null ? '#6b7280' : v >= 85 ? '#c9a84c' : v >= 65 ? '#a07830' : '#1a1a1a';
const scoreColor = v => v == null ? '#6b7280' : v >= 8 ? '#c9a84c' : v >= 6 ? '#a07830' : '#1a1a1a';
const riskColor = n => n === 0 ? '#c9a84c' : n <= 3 ? '#a07830' : '#1a1a1a';

// ── API helpers ────────────────────────────────────────────────────────────
const apiFetch = (path, opts) => fetch(API + path, opts).then(r => r.json());

// ── Small shared components ────────────────────────────────────────────────
const SectionLabel = ({
  children,
  mt = false
}) => /*#__PURE__*/React.createElement("div", {
  className: `text-xs font-bold uppercase tracking-widest text-gold-dark border-b border-gray-200 pb-2 ${mt ? 'mt-6' : ''} mb-4`
}, children);
const StatCard = ({
  num,
  label,
  color = '#3b82f6',
  small = false
}) => /*#__PURE__*/React.createElement("div", {
  className: "bg-gray-50 border border-gray-200 rounded-2xl p-4 text-center hover:border-gold-border transition-all card-hover stat-shimmer"
}, /*#__PURE__*/React.createElement("div", {
  className: `font-extrabold leading-none ${small ? 'text-2xl' : 'text-3xl'}`,
  style: {
    color
  }
}, num), /*#__PURE__*/React.createElement("div", {
  className: "text-xs font-bold uppercase tracking-widest text-gray-400 mt-2"
}, label));
const Badge = ({
  label,
  type = 'neutral'
}) => {
  const map = {
    green: 'bg-gold-light text-gold-dark border-gold-border',
    amber: 'bg-gold-light text-gold-dark border-gold-border',
    red: 'bg-gray-900 text-white border-gray-800',
    blue: 'bg-gold-light text-gold-dark border-gold-border',
    neutral: 'bg-gray-100 text-gray-600 border-gray-200'
  };
  return /*#__PURE__*/React.createElement("span", {
    className: `inline-block px-2 py-0.5 rounded text-xs font-semibold border ${map[type] || map.neutral}`
  }, label);
};
const FieldCard = ({
  label,
  value,
  color = '#3b82f6'
}) => /*#__PURE__*/React.createElement("div", {
  className: "bg-gray-50 border border-gray-200 rounded-xl p-4 mb-3",
  style: {
    borderLeft: `4px solid ${color}`
  }
}, /*#__PURE__*/React.createElement("div", {
  className: "text-xs font-bold uppercase tracking-wider mb-2",
  style: {
    color
  }
}, label), Array.isArray(value) ? /*#__PURE__*/React.createElement("div", null, value.filter(Boolean).map((v, i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  className: "flex gap-2 py-1 border-b border-gray-100 last:border-0 text-sm text-gray-800"
}, /*#__PURE__*/React.createElement("span", {
  style: {
    color
  },
  className: "font-bold mt-0.5"
}, "\u203A"), v))) : /*#__PURE__*/React.createElement("div", {
  className: "text-sm font-medium text-gray-900"
}, value || '—'));
const Chip = ({
  label,
  color = 'gold'
}) => {
  const s = {
    gold: 'bg-gold-light text-gold-dark border-gold-border',
    green: 'bg-green-50 text-green-700 border-green-200'
  };
  return /*#__PURE__*/React.createElement("span", {
    className: `inline-block border rounded px-2.5 py-0.5 text-xs font-semibold mr-1.5 mb-1 ${s[color] || s.gold}`
  }, label);
};
const PillList = ({
  title,
  items,
  accent
}) => /*#__PURE__*/React.createElement("div", {
  className: "rounded-xl border p-4",
  style: {
    background: '#fdf8ee',
    borderColor: 'rgba(201,168,76,0.35)'
  }
}, /*#__PURE__*/React.createElement("div", {
  className: "text-xs font-bold uppercase tracking-wider mb-3",
  style: {
    color: accent === 'green' ? '#c9a84c' : '#1a1a1a'
  }
}, title), items.filter(Boolean).map((x, i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  className: "flex gap-2 py-1.5 border-b last:border-0 text-sm",
  style: {
    borderColor: 'rgba(201,168,76,0.2)'
  }
}, /*#__PURE__*/React.createElement("span", {
  className: "font-bold mt-0.5",
  style: {
    color: accent === 'green' ? '#c9a84c' : '#1a1a1a'
  }
}, "\u203A"), /*#__PURE__*/React.createElement("span", {
  className: "text-gray-800"
}, x))));
const NumberedList = ({
  title,
  items,
  accent = 'gold'
}) => {
  const c = {
    gold: '#a07830',
    green: '#c9a84c'
  };
  const bg = {
    gold: '#fdf8ee',
    green: '#fdf8ee'
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "bg-gray-50 border border-gray-200 rounded-xl p-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-wider mb-3",
    style: {
      color: c[accent]
    }
  }, title), items.filter(Boolean).map((x, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "flex gap-3 py-1.5 border-b border-gray-100 last:border-0 items-start"
  }, /*#__PURE__*/React.createElement("span", {
    className: "w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-extrabold mt-0.5",
    style: {
      background: bg[accent],
      color: c[accent]
    }
  }, i + 1), /*#__PURE__*/React.createElement("span", {
    className: "text-sm text-gray-800 leading-relaxed"
  }, x))));
};
const Collapsible = ({
  title,
  icon,
  children,
  defaultOpen = true
}) => {
  const [open, setOpen] = useState(defaultOpen);
  return /*#__PURE__*/React.createElement("div", {
    className: "bg-gray-50 border border-gray-200 rounded-2xl overflow-hidden"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setOpen(v => !v),
    className: "w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-100 transition-all"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2 text-gold-dark"
  }, icon, /*#__PURE__*/React.createElement("span", {
    className: "text-xs font-bold uppercase tracking-widest"
  }, title)), open ? /*#__PURE__*/React.createElement(IcoChevD, {
    s: 13,
    c: "text-gray-400"
  }) : /*#__PURE__*/React.createElement(IcoChevR, {
    s: 13,
    c: "text-gray-400"
  })), open && /*#__PURE__*/React.createElement("div", {
    className: "px-4 pb-4"
  }, children));
};

// ── Sidebar ────────────────────────────────────────────────────────────────
const NAV = [{
  id: 'home',
  label: 'Home',
  Icon: IcoHome
}, {
  id: 'recordings',
  label: 'Recordings',
  Icon: IcoFiles
}, {
  id: 'live',
  label: 'Live',
  Icon: IcoLive
}, {
  id: 'calendar',
  label: 'Calendar',
  Icon: IcoCal
}, {
  id: 'requirements',
  label: 'Requirements',
  Icon: IcoReq
}];
const Sidebar = ({
  page,
  setPage,
  recordings,
  serverOk,
  collapsed,
  onToggle
}) => {
  const totalMin = countMinutes(recordings);
  const usedPct = Math.min(Math.round(totalMin / 300 * 100), 100);
  return /*#__PURE__*/React.createElement("div", {
    className: `${collapsed ? 'w-14' : 'w-60'} flex-shrink-0 bg-gray-50 border-r border-gray-200 flex flex-col h-screen sticky top-0 overflow-hidden transition-all duration-200`,
    style: {
      minWidth: collapsed ? '3.5rem' : '15rem'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: `flex items-center border-b border-gray-200 px-3 py-4 ${collapsed ? 'justify-center' : 'justify-between'}`
  }, !collapsed && /*#__PURE__*/React.createElement("div", {
    className: "min-w-0 mr-2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-base font-extrabold text-gold-dark tracking-tight leading-tight truncate"
  }, "Clario"), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 uppercase tracking-widest mt-0.5 truncate"
  }, "Meeting Intelligence")), /*#__PURE__*/React.createElement("button", {
    onClick: onToggle,
    title: collapsed ? 'Expand sidebar' : 'Collapse sidebar',
    className: "p-2 rounded-lg hover:bg-gray-200 text-gray-400 hover:text-gold-dark transition-all flex-shrink-0"
  }, /*#__PURE__*/React.createElement(IcoPanelLeft, {
    s: 16
  }))), /*#__PURE__*/React.createElement("nav", {
    className: `flex-1 p-2 ${collapsed ? 'flex flex-col items-center gap-1' : ''}`
  }, NAV.map(({
    id,
    label,
    Icon
  }) => /*#__PURE__*/React.createElement("button", {
    key: id,
    onClick: () => setPage(id),
    title: collapsed ? label : undefined,
    className: `flex items-center rounded-lg font-medium transition-all
              ${collapsed ? 'w-10 h-10 justify-center' : 'w-full gap-3 px-3 py-2.5 mb-0.5 text-sm text-left'}
              ${page === id ? 'bg-gold-light text-gold-dark border border-gold-border' : 'text-gray-600 hover:bg-gray-100 hover:text-gold-dark border border-transparent'}`
  }, /*#__PURE__*/React.createElement(Icon, {
    s: 15
  }), !collapsed && label))), collapsed ? /*#__PURE__*/React.createElement("div", {
    className: "py-4 flex flex-col items-center gap-2 border-t border-gray-200"
  }, /*#__PURE__*/React.createElement("span", {
    className: `w-2 h-2 rounded-full ${serverOk ? 'bg-gold' : 'bg-gray-900'}`,
    title: serverOk ? 'Server online' : 'Server offline'
  })) : /*#__PURE__*/React.createElement("div", {
    className: "px-4 py-4 border-t border-gray-200"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-wider text-gray-400 mb-2"
  }, "Usage"), /*#__PURE__*/React.createElement("div", {
    className: "h-1.5 bg-gray-200 rounded-full overflow-hidden mb-1.5"
  }, /*#__PURE__*/React.createElement("div", {
    className: "h-full bg-gold rounded-full transition-all",
    style: {
      width: `${usedPct}%`
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400"
  }, totalMin, " / 300 min"), /*#__PURE__*/React.createElement("div", {
    className: `flex items-center gap-1.5 mt-3 text-xs ${serverOk ? 'text-gold-dark' : 'text-gray-900'}`
  }, /*#__PURE__*/React.createElement("span", {
    className: `w-2 h-2 rounded-full ${serverOk ? 'bg-gold' : 'bg-gray-900'}`
  }), serverOk ? 'Server online' : 'Server offline')));
};

// ── Recording Card ─────────────────────────────────────────────────────────
const RecordingCard = ({
  rec,
  onOpen
}) => {
  const id = rec.job_id || '';
  const title = prettify(id);
  const date = parseDate(id);
  const dur = getDuration(rec.transcript);
  const f = rec.extracted_fields || {};
  const risks = rec.risk_report?.risks || [];
  const conf = f.conformance_score;
  const callS = f.call_score;
  const accentColor = riskColor(risks.length);
  return /*#__PURE__*/React.createElement("div", {
    className: "bg-white border border-gray-200 rounded-2xl p-5 mb-3 hover:border-gold-border transition-all cursor-pointer fade-in group card-hover recording-card",
    style: {
      borderLeft: `4px solid ${accentColor}`
    },
    onClick: () => onOpen(id)
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-start justify-between gap-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex-1 min-w-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "font-bold text-gray-900 text-base truncate"
  }, title), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 mt-1"
  }, date || 'Unknown date', dur && dur !== '-' ? ` · ${dur}` : ''), /*#__PURE__*/React.createElement("div", {
    className: "flex flex-wrap gap-2 mt-3 items-center"
  }, conf != null && /*#__PURE__*/React.createElement(Badge, {
    label: `${Math.round(Number(conf))}% SOP`,
    type: conf >= 85 ? 'green' : conf >= 65 ? 'amber' : 'red'
  }), callS != null && /*#__PURE__*/React.createElement(Badge, {
    label: `${Number(callS).toFixed(1)}/10`,
    type: callS >= 8 ? 'green' : callS >= 6 ? 'amber' : 'red'
  }), /*#__PURE__*/React.createElement(Badge, {
    label: risks.length ? `${risks.length} risk${risks.length > 1 ? 's' : ''}` : 'Clear',
    type: risks.length === 0 ? 'green' : risks.length <= 3 ? 'amber' : 'red'
  })), f.call_summary && /*#__PURE__*/React.createElement("p", {
    className: "text-xs text-gray-400 italic mt-2 line-clamp-1"
  }, f.call_summary)), /*#__PURE__*/React.createElement("button", {
    className: "flex items-center gap-1 text-xs font-semibold text-gold-dark border border-gold-border rounded-lg px-3 py-1.5 hover:bg-gold-light transition-all flex-shrink-0 group-hover:border-gold"
  }, "View ", /*#__PURE__*/React.createElement(IcoChevR, {
    s: 13
  }))));
};

// ── Upload Section ─────────────────────────────────────────────────────────
const UploadSection = ({
  onProcessed
}) => {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [msg, setMsg] = useState('');
  const [drag, setDrag] = useState(false);
  const ref = useRef();
  const handleFile = f => {
    if (f) setFile(f);
  };
  const onDrop = e => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };
  const process = async () => {
    if (!file) return;
    try {
      setStatus('uploading');
      setMsg('Uploading…');
      const fd = new FormData();
      fd.append('file', file);
      const up = await fetch(`${API}/api/upload-recording`, {
        method: 'POST',
        body: fd
      }).then(r => r.json());
      setStatus('processing');
      setMsg('Processing with AI (this may take a minute)…');
      const proc = await apiFetch(`/api/process?filename=${encodeURIComponent(up.filename)}`);
      const jobId = proc.job_id;
      for (let i = 0; i < 120; i++) {
        await new Promise(r => setTimeout(r, 3000));
        const s = await apiFetch(`/api/process-status/${jobId}`);
        if (s.status === 'done') {
          setStatus('done');
          setMsg(`Done — "${prettify(jobId)}" is ready.`);
          setFile(null);
          onProcessed(jobId);
          return;
        }
        if (s.status === 'error') {
          setStatus('error');
          setMsg(s.error || 'Processing failed');
          return;
        }
      }
      setStatus('error');
      setMsg('Timed out — check server logs.');
    } catch (e) {
      setStatus('error');
      setMsg(String(e));
    }
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold-dark mb-1"
  }, "Upload Recording"), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 mb-3"
  }, "MP4, MOV, WAV, MP3, WebM \u2014 transcribed automatically"), /*#__PURE__*/React.createElement("div", {
    onDragOver: e => {
      e.preventDefault();
      setDrag(true);
    },
    onDragLeave: () => setDrag(false),
    onDrop: onDrop,
    className: `border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${drag || file ? 'border-gold bg-gold-light' : 'border-gray-200 hover:border-gold-border'}`,
    onClick: () => ref.current?.click()
  }, /*#__PURE__*/React.createElement("input", {
    ref: ref,
    type: "file",
    accept: ".mp4,.webm,.mkv,.mov,.avi,.wav,.mp3,.m4a",
    className: "hidden",
    onChange: e => handleFile(e.target.files[0])
  }), /*#__PURE__*/React.createElement(IcoUpload, {
    s: 22,
    c: "mx-auto mb-2 text-gray-400"
  }), file ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-semibold text-gray-800 truncate"
  }, file.name), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400"
  }, (file.size / 1048576).toFixed(1), " MB")) : /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-gray-400"
  }, "Drop file here or click to browse")), file && status !== 'uploading' && status !== 'processing' && /*#__PURE__*/React.createElement("button", {
    onClick: process,
    className: "w-full mt-3 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-gold-dark to-gold hover:opacity-90 transition-all btn-gold-shine"
  }, "Process Recording"), (status === 'uploading' || status === 'processing') && /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2 mt-3 text-sm text-gold-dark"
  }, /*#__PURE__*/React.createElement(IcoSpin, {
    s: 15
  }), msg), status === 'done' && /*#__PURE__*/React.createElement("div", {
    className: "mt-3 text-xs text-gold-dark font-medium"
  }, msg), status === 'error' && /*#__PURE__*/React.createElement("div", {
    className: "mt-3 text-xs text-gray-900 font-medium"
  }, msg));
};

// ── Agent Join Panel ──────────────────────────────────────────────────────
const AgentPanel = () => {
  const [meetings, setMeetings] = useState([]);
  const [url, setUrl] = useState('');
  const [platform, setPlatform] = useState(null);
  const [agentSt, setAgentSt] = useState({
    status: 'stopped',
    uptime_sec: 0,
    sessions_handled: 0
  });
  const [joiningId, setJoiningId] = useState(null); // null | 'manual' | meeting index
  const [msg, setMsg] = useState('');
  const stColor = {
    running: 'text-gold-dark',
    starting: 'text-gold',
    idle: 'text-gray-600',
    stopped: 'text-gray-400'
  };
  const platLabel = {
    meet: 'Google Meet',
    zoom: 'Zoom',
    teams: 'Teams'
  };
  const platColor = {
    meet: 'text-gold-dark',
    zoom: 'text-gray-700',
    teams: 'text-gray-600'
  };

  // Poll agent status every 5s
  useEffect(() => {
    const poll = () => apiFetch('/api/agent-status').then(s => setAgentSt(s)).catch(() => {});
    poll();
    const iv = setInterval(poll, 5000);
    return () => clearInterval(iv);
  }, []);

  // Fetch calendar meetings every 30s
  useEffect(() => {
    const load = () => apiFetch('/api/upcoming-meetings').then(data => setMeetings(Array.isArray(data) ? data : [])).catch(() => {});
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);
  useEffect(() => {
    const u = url.toLowerCase();
    if (u.includes('meet.google.com')) setPlatform('meet');else if (u.includes('zoom.us')) setPlatform('zoom');else if (u.includes('teams.microsoft.com') || u.includes('teams.live.com')) setPlatform('teams');else setPlatform(null);
  }, [url]);
  const isActive = agentSt.status === 'running' || agentSt.status === 'starting';
  const fmt = t => {
    try {
      return new Date(t).toLocaleTimeString('en', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return t;
    }
  };
  const doJoin = async (meetUrl, meetPlatform, title, joinKey) => {
    setJoiningId(joinKey);
    setMsg('');
    try {
      const r = await apiFetch('/api/join-now', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          meeting_url: meetUrl,
          platform: meetPlatform,
          title: title || 'Meeting'
        })
      });
      if (r.error) setMsg('Error: ' + r.error);else {
        setMsg('Bot is joining…');
        setUrl('');
      }
    } catch (e) {
      setMsg('Failed: ' + String(e));
    } finally {
      setJoiningId(null);
    }
  };
  const stopNow = async () => {
    await apiFetch('/api/agent-stop', {
      method: 'POST'
    }).catch(() => {});
    setMsg('Stop signal sent.');
    setAgentSt(s => ({
      ...s,
      status: 'stopped'
    }));
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between mb-3"
  }, /*#__PURE__*/React.createElement("span", {
    className: `text-xs font-bold ${stColor[agentSt.status] || 'text-gray-400'}`
  }, "\u25CF ", agentSt.status), isActive && /*#__PURE__*/React.createElement("button", {
    onClick: stopNow,
    className: "text-xs text-red-500 border border-red-200 rounded px-2 py-0.5 hover:bg-red-50 transition-all"
  }, "Stop")), isActive && /*#__PURE__*/React.createElement("div", {
    className: "bg-gold-light border border-gold-border rounded-lg p-2.5 text-xs mb-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-gold-dark font-semibold"
  }, "Bot is in a meeting"), agentSt.uptime_sec > 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-gold mt-0.5"
  }, Math.floor(agentSt.uptime_sec / 60), "m ", agentSt.uptime_sec % 60, "s uptime \xB7 ", agentSt.sessions_handled || 0, " session", agentSt.sessions_handled !== 1 ? 's' : '')), !isActive && /*#__PURE__*/React.createElement(React.Fragment, null, meetings.length > 0 ? /*#__PURE__*/React.createElement("div", {
    className: "mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold text-gray-400 uppercase tracking-wider mb-2"
  }, "From your calendar"), meetings.slice(0, 4).map((m, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "flex items-center gap-2 py-2 border-b border-gray-100 last:border-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex-1 min-w-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-medium text-gray-900 truncate"
  }, m.title || 'Meeting'), /*#__PURE__*/React.createElement("div", {
    className: `text-xs ${platColor[m.platform] || 'text-gray-400'}`
  }, fmt(m.start_time), " \xB7 ", m.platform)), m.join_url && /*#__PURE__*/React.createElement("button", {
    onClick: () => doJoin(m.join_url, m.platform, m.title, i),
    disabled: joiningId !== null,
    className: "flex-shrink-0 px-3 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-gold-dark to-gold rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center gap-1 btn-gold-shine"
  }, joiningId === i ? /*#__PURE__*/React.createElement(IcoSpin, {
    s: 11
  }) : /*#__PURE__*/React.createElement(IcoLive, {
    s: 11
  }), joiningId === i ? '…' : 'Join')))) : /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 mb-3 bg-gray-50 border border-gray-200 rounded-lg p-3"
  }, "No meetings found in calendar.", /*#__PURE__*/React.createElement("br", null), /*#__PURE__*/React.createElement("span", {
    className: "text-gold-dark font-medium"
  }, "Paste a URL below"), " to join manually."), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 mb-1.5"
  }, "Join by URL:"), /*#__PURE__*/React.createElement("div", {
    className: "relative mb-2"
  }, /*#__PURE__*/React.createElement(IcoLink, {
    s: 13,
    c: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
  }), /*#__PURE__*/React.createElement("input", {
    value: url,
    onChange: e => setUrl(e.target.value),
    placeholder: "https://meet.google.com/\u2026",
    className: "w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gold transition-all"
  })), platform && /*#__PURE__*/React.createElement("div", {
    className: "mb-2 text-xs text-gold-dark font-medium"
  }, platLabel[platform], " detected"), url && !platform && /*#__PURE__*/React.createElement("div", {
    className: "mb-2 text-xs text-gray-900 font-medium"
  }, "Unrecognised URL"), platform && /*#__PURE__*/React.createElement("button", {
    onClick: () => doJoin(url, platform, 'Manual Join', 'manual'),
    disabled: joiningId !== null,
    className: "w-full py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-gold-dark to-gold hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 btn-gold-shine"
  }, joiningId === 'manual' ? /*#__PURE__*/React.createElement(IcoSpin, {
    s: 14
  }) : /*#__PURE__*/React.createElement(IcoLive, {
    s: 14
  }), joiningId === 'manual' ? 'Starting…' : 'Join & Record')), msg && /*#__PURE__*/React.createElement("div", {
    className: "mt-2 text-xs text-gray-500"
  }, msg));
};

// ── Upcoming Meetings ──────────────────────────────────────────────────────
const UpcomingMeetings = () => {
  const [meetings, setMeetings] = useState([]);
  useEffect(() => {
    apiFetch('/api/upcoming-meetings').then(setMeetings).catch(() => {});
  }, []);
  const fmt = t => {
    try {
      return new Date(t).toLocaleTimeString('en', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return t;
    }
  };
  const platColors = {
    meet: 'bg-gold-light text-gold-dark',
    zoom: 'bg-gray-100 text-gray-700',
    teams: 'bg-gray-100 text-gray-600'
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold-dark mb-3"
  }, "Upcoming Meetings"), meetings.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400"
  }, "No upcoming meetings detected \u2014 ensure the agent is running.") : meetings.slice(0, 4).map((m, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-medium text-gray-900 truncate max-w-[140px]"
  }, m.title || 'Meeting'), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400"
  }, fmt(m.start_time))), /*#__PURE__*/React.createElement("span", {
    className: `text-xs font-semibold px-2 py-0.5 rounded-full ${platColors[m.platform] || 'bg-gray-100 text-gray-600'}`
  }, m.platform))));
};

// ── Home Dashboard ─────────────────────────────────────────────────────────
const QuickAction = ({
  icon,
  label,
  desc,
  onClick,
  color = '#c9a84c'
}) => /*#__PURE__*/React.createElement("button", {
  onClick: onClick,
  className: "flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-2xl hover:border-gold-border transition-all text-left w-full card-hover"
}, /*#__PURE__*/React.createElement("div", {
  className: "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0",
  style: {
    background: `${color}18`,
    color
  }
}, icon), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
  className: "text-sm font-bold text-gray-900"
}, label), /*#__PURE__*/React.createElement("div", {
  className: "text-xs text-gray-400"
}, desc)), /*#__PURE__*/React.createElement(IcoChevR, {
  s: 14,
  c: "ml-auto text-gray-300"
}));
const HomeDashboard = ({
  recordings,
  onOpen,
  onProcessed,
  setPage,
  serverOk
}) => {
  const needsReview = recordings.filter(r => r.risk_report?.needs_review).length;
  const thisWeek = recordings.filter(r => {
    const m = r.job_id?.match(/(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return false;
    const d = new Date(+m[1], +m[2] - 1, +m[3]);
    return Date.now() - d.getTime() < 7 * 86400000;
  }).length;
  const avgConf = recordings.length ? Math.round(recordings.reduce((s, r) => {
    const v = r.extracted_fields?.conformance_score;
    return v != null ? s + Number(v) : s;
  }, 0) / Math.max(1, recordings.filter(r => r.extracted_fields?.conformance_score != null).length)) : null;
  const recent = recordings.slice(0, 3);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  return /*#__PURE__*/React.createElement("div", {
    className: "p-6 max-w-4xl"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mb-7"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold-dark mb-1"
  }, "Dashboard"), /*#__PURE__*/React.createElement("h1", {
    className: "text-2xl font-extrabold text-gray-900"
  }, greeting), /*#__PURE__*/React.createElement("p", {
    className: "text-sm text-gray-400 mt-1"
  }, new Date().toLocaleDateString('en', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  }))), /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-4 gap-3 mb-8"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-3xl font-extrabold text-gold-dark leading-none"
  }, recordings.length), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold mt-2"
  }, "Total Calls")), /*#__PURE__*/React.createElement("div", {
    className: "bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-3xl font-extrabold text-gray-900 leading-none"
  }, countMinutes(recordings)), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold mt-2"
  }, "Minutes")), /*#__PURE__*/React.createElement("div", {
    className: "bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-3xl font-extrabold leading-none",
    style: {
      color: '#a07830'
    }
  }, avgConf != null ? `${avgConf}%` : '—'), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold-dark mt-2"
  }, "Avg SOP")), /*#__PURE__*/React.createElement("div", {
    className: "bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-3xl font-extrabold leading-none text-gray-900"
  }, needsReview), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest mt-2 text-gold"
  }, "Needs Review"))), /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-[1fr_280px] gap-6"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold-dark"
  }, "Recent Recordings"), recordings.length > 3 && /*#__PURE__*/React.createElement("button", {
    onClick: () => setPage('recordings'),
    className: "text-xs font-semibold text-gold-dark hover:text-gold border border-gold-border rounded-lg px-3 py-1 hover:bg-gold-light transition-all"
  }, "View all ", recordings.length, " \u2192")), recent.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "border-2 border-dashed border-gray-200 rounded-2xl p-12 text-center"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-4xl mb-3"
  }, "\uD83C\uDF99"), /*#__PURE__*/React.createElement("div", {
    className: "font-semibold text-gray-700 mb-1"
  }, "No recordings yet"), /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-gray-400"
  }, "Upload your first call recording to get started")) : recent.map(r => /*#__PURE__*/React.createElement(RecordingCard, {
    key: r.job_id,
    rec: r,
    onOpen: onOpen
  })), thisWeek > 0 && /*#__PURE__*/React.createElement("div", {
    className: "mt-4 text-xs text-gray-400 flex items-center gap-1.5"
  }, /*#__PURE__*/React.createElement("span", {
    className: "w-2 h-2 rounded-full bg-green-400 inline-block"
  }), thisWeek, " recording", thisWeek > 1 ? 's' : '', " this week")), /*#__PURE__*/React.createElement("div", {
    className: "space-y-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gold-dark mb-4"
  }, "Quick Actions"), /*#__PURE__*/React.createElement(QuickAction, {
    icon: /*#__PURE__*/React.createElement(IcoUpload, {
      s: 18
    }),
    label: "Upload Recording",
    desc: "Process a call with AI",
    onClick: () => setPage('recordings'),
    color: "#c9a84c"
  }), /*#__PURE__*/React.createElement(QuickAction, {
    icon: /*#__PURE__*/React.createElement(IcoLive, {
      s: 18
    }),
    label: "Live Transcription",
    desc: "Transcribe mic or screen",
    onClick: () => setPage('live'),
    color: "#c9a84c"
  }), /*#__PURE__*/React.createElement(QuickAction, {
    icon: /*#__PURE__*/React.createElement(IcoCal, {
      s: 18
    }),
    label: "Calendar",
    desc: "Connect & auto-join meetings",
    onClick: () => setPage('calendar'),
    color: "#a07830"
  }), /*#__PURE__*/React.createElement(QuickAction, {
    icon: /*#__PURE__*/React.createElement(IcoReq, {
      s: 18
    }),
    label: "Requirements",
    desc: "View extracted requirements",
    onClick: () => setPage('requirements'),
    color: "#c9a84c"
  }), needsReview > 0 && /*#__PURE__*/React.createElement("div", {
    className: "mt-2 bg-gray-900 border border-gray-700 rounded-xl p-3 text-xs text-white font-medium"
  }, needsReview, " recording", needsReview > 1 ? 's' : '', " flagged for review"))));
};

// ── Recordings Page ────────────────────────────────────────────────────────
const RecordingsPage = ({
  recordings,
  onOpen,
  onProcessed
}) => {
  const [q, setQ] = useState('');
  const filtered = q ? recordings.filter(r => (r.job_id || '').toLowerCase().includes(q.toLowerCase()) || (r.extracted_fields?.client_name || '').toLowerCase().includes(q.toLowerCase())) : recordings;
  const needsReview = recordings.filter(r => r.risk_report?.needs_review).length;
  return /*#__PURE__*/React.createElement("div", {
    className: "p-6"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mb-6 flex items-start justify-between"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    className: "text-2xl font-extrabold text-gray-900"
  }, "All Recordings"), /*#__PURE__*/React.createElement("p", {
    className: "text-sm text-gray-400 mt-1"
  }, recordings.length, " total \xB7 ", needsReview, " flagged")), /*#__PURE__*/React.createElement("div", {
    className: "relative"
  }, /*#__PURE__*/React.createElement(IcoSearch, {
    s: 14,
    c: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
  }), /*#__PURE__*/React.createElement("input", {
    value: q,
    onChange: e => setQ(e.target.value),
    placeholder: "Search recordings\u2026",
    className: "pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gold transition-all w-56"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-3 gap-3 mb-6"
  }, /*#__PURE__*/React.createElement(StatCard, {
    num: recordings.length,
    label: "Total",
    color: "#c9a84c",
    small: true
  }), /*#__PURE__*/React.createElement(StatCard, {
    num: countMinutes(recordings),
    label: "Minutes",
    color: "#a07830",
    small: true
  }), /*#__PURE__*/React.createElement(StatCard, {
    num: needsReview,
    label: "Needs Review",
    color: needsReview ? '#1a1a1a' : '#c9a84c',
    small: true
  })), filtered.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "border border-gray-200 rounded-2xl p-16 text-center"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-gray-300 text-5xl mb-4"
  }, "\uD83D\uDD0D"), /*#__PURE__*/React.createElement("div", {
    className: "font-semibold text-gray-700"
  }, "No matches"), /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-gray-400 mt-2"
  }, q ? 'Try a different search term' : 'Upload a recording using the panel on the right')) : filtered.map(r => /*#__PURE__*/React.createElement(RecordingCard, {
    key: r.job_id,
    rec: r,
    onOpen: onOpen
  })));
};

// ══════════════════════════════════════════════════════════════════════════
//  ANALYSIS DASHBOARD
// ══════════════════════════════════════════════════════════════════════════

const TopBar = ({
  rec,
  onBack,
  onReanalyze,
  reanalyzing
}) => {
  const id = rec.job_id || '';
  return /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-4 px-6 py-4 border-b border-gray-200 bg-white sticky top-0 z-10"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onBack,
    className: "flex items-center gap-1.5 text-sm text-gray-500 hover:text-gold-dark transition-all"
  }, /*#__PURE__*/React.createElement(IcoBack, {
    s: 16
  }), " Back"), /*#__PURE__*/React.createElement("div", {
    className: "flex-1 min-w-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "font-bold text-lg text-gray-900 truncate"
  }, prettify(id)), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400"
  }, parseDate(id) || 'Unknown date', " \xB7 ", getDuration(rec.transcript))), /*#__PURE__*/React.createElement("button", {
    onClick: onReanalyze,
    disabled: reanalyzing,
    className: "flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gold-dark border border-gold-border rounded-lg hover:bg-gold-light transition-all disabled:opacity-50"
  }, reanalyzing ? /*#__PURE__*/React.createElement(IcoSpin, {
    s: 13
  }) : /*#__PURE__*/React.createElement(IcoRefresh, {
    s: 13
  }), " Re-analyze"), /*#__PURE__*/React.createElement("a", {
    href: `${API}/api/recordings/${id}/pdf`,
    target: "_blank",
    rel: "noreferrer",
    className: "flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-gold-dark to-gold rounded-lg hover:opacity-90 transition-all btn-gold-shine"
  }, /*#__PURE__*/React.createElement(IcoDl, {
    s: 13
  }), " Download PDF"));
};
const ScoreStrip = ({
  f,
  risks,
  needsReview
}) => {
  const conf = f.conformance_score;
  const callS = f.call_score;
  const indS = f.individual_score;
  const items = [{
    num: conf != null ? `${Math.round(Number(conf))}%` : '—',
    label: 'Conformance',
    sub: f.conformance_status || '',
    color: confColor(conf)
  }, {
    num: callS != null ? `${Number(callS).toFixed(1)}/10` : '—',
    label: 'Call Quality',
    sub: (f.call_rating || '').toLowerCase(),
    color: scoreColor(callS)
  }, {
    num: indS != null ? `${Number(indS).toFixed(1)}/10` : '—',
    label: 'Individual',
    sub: '',
    color: scoreColor(indS)
  }, {
    num: risks.length,
    label: 'Risk Items',
    sub: needsReview ? 'Needs Review' : 'Clear',
    color: riskColor(risks.length)
  }];
  return /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-4 gap-4 px-6 py-4 border-b border-gray-100"
  }, items.map(({
    num,
    label,
    sub,
    color
  }, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "bg-gray-50 border border-gray-200 rounded-2xl p-4 text-center hover:border-gold-border transition-all"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-2xl font-extrabold",
    style: {
      color
    }
  }, num), /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-bold uppercase tracking-widest text-gray-400 mt-1"
  }, label), sub && /*#__PURE__*/React.createElement("div", {
    className: "text-xs font-semibold mt-1.5 uppercase tracking-wider",
    style: {
      color
    }
  }, sub))));
};
const TabOverview = ({
  f
}) => /*#__PURE__*/React.createElement("div", {
  className: "fade-in"
}, /*#__PURE__*/React.createElement(SectionLabel, null, "Meeting Information"), /*#__PURE__*/React.createElement("div", {
  className: "grid grid-cols-2 gap-3 mb-2"
}, /*#__PURE__*/React.createElement(FieldCard, {
  label: "Client / Account",
  value: f.client_name,
  color: "#c9a84c"
}), /*#__PURE__*/React.createElement(FieldCard, {
  label: "Client Problem",
  value: f.client_problem,
  color: "#a07830"
}), /*#__PURE__*/React.createElement(FieldCard, {
  label: "Timeline",
  value: f.timeline,
  color: "#1a1a1a"
}), /*#__PURE__*/React.createElement(FieldCard, {
  label: "Budget",
  value: f.budget,
  color: "#c9a84c"
})), f.call_summary && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SectionLabel, {
  mt: true
}, "Call Summary"), /*#__PURE__*/React.createElement("div", {
  className: "bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-800 leading-relaxed mb-2"
}, f.call_summary)), (f.call_highlights?.length || f.call_concerns?.length) && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SectionLabel, {
  mt: true
}, "Highlights & Concerns"), /*#__PURE__*/React.createElement("div", {
  className: "grid grid-cols-2 gap-3 mb-2"
}, f.call_highlights?.length ? /*#__PURE__*/React.createElement(PillList, {
  title: "Highlights",
  items: f.call_highlights,
  accent: "green"
}) : /*#__PURE__*/React.createElement("div", null), f.call_concerns?.length ? /*#__PURE__*/React.createElement(PillList, {
  title: "Concerns",
  items: f.call_concerns,
  accent: "red"
}) : /*#__PURE__*/React.createElement("div", null))), (f.call_insights?.length || f.next_steps?.length) && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SectionLabel, {
  mt: true
}, "Insights & Next Actions"), /*#__PURE__*/React.createElement("div", {
  className: "grid grid-cols-2 gap-3 mb-2"
}, f.call_insights?.length ? /*#__PURE__*/React.createElement(NumberedList, {
  title: "Key Insights",
  items: f.call_insights,
  accent: "gold"
}) : /*#__PURE__*/React.createElement("div", null), f.next_steps?.length ? /*#__PURE__*/React.createElement(NumberedList, {
  title: "Next Actions",
  items: f.next_steps,
  accent: "green"
}) : /*#__PURE__*/React.createElement("div", null))), f.conclusions && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SectionLabel, {
  mt: true
}, "Conclusions"), /*#__PURE__*/React.createElement("div", {
  className: "bg-amber-50 border border-amber-200 rounded-xl p-5 text-sm text-gray-800 leading-relaxed",
  style: {
    borderLeft: '4px solid #c9a84c'
  }
}, f.conclusions)), f.techstack_platform?.length && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SectionLabel, {
  mt: true
}, "Tech Stack"), /*#__PURE__*/React.createElement("div", {
  className: "bg-gray-50 border border-gray-200 rounded-xl p-4"
}, (Array.isArray(f.techstack_platform) ? f.techstack_platform : [f.techstack_platform]).filter(Boolean).map((t, i) => /*#__PURE__*/React.createElement(Chip, {
  key: i,
  label: t
})))));
const SOP_SECTIONS = [['Call Opening', 15, 'Professional greeting · Purpose clearly stated · Agenda set'], ['Needs Discovery', 20, 'Primary pain point identified · Open-ended questions asked · Understanding confirmed'], ['Qualification', 15, 'Budget explored · Timeline discussed · Decision-makers identified'], ['Solution Alignment', 20, 'Solution matched to problem · Technical requirements discussed · Value proposition communicated'], ['Objection Handling', 15, 'All objections acknowledged · Responded with evidence · Client satisfaction confirmed'], ['Call Closing', 15, 'Next steps defined · Follow-up timeline agreed · Positive close']];
const TabConformance = ({
  f
}) => {
  const [sopOpen, setSopOpen] = useState(false);
  const conf = f.conformance_score;
  const pct = conf != null ? Math.round(Number(conf)) : null;
  const color = confColor(conf);
  const passed = f.conformance_passed || [];
  const missed = f.conformance_missed || [];
  return /*#__PURE__*/React.createElement("div", {
    className: "fade-in"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "SOP Score"), pct != null && /*#__PURE__*/React.createElement("div", {
    className: "bg-gray-50 border border-gray-200 rounded-xl p-5 mb-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-end gap-3 mb-3"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-4xl font-extrabold",
    style: {
      color
    }
  }, pct), /*#__PURE__*/React.createElement("span", {
    className: "text-gray-400 text-lg mb-1"
  }, "/100"), /*#__PURE__*/React.createElement("span", {
    className: "ml-2 text-sm font-bold uppercase tracking-widest",
    style: {
      color
    }
  }, f.conformance_status || '')), /*#__PURE__*/React.createElement("div", {
    className: "h-2.5 bg-gray-200 rounded-full overflow-hidden"
  }, /*#__PURE__*/React.createElement("div", {
    className: "h-full rounded-full transition-all",
    style: {
      width: `${pct}%`,
      background: color
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "flex gap-4 mt-3 text-xs text-gray-400"
  }, /*#__PURE__*/React.createElement("span", null, "PASS \u2265 85"), /*#__PURE__*/React.createElement("span", null, "REVIEW 65\u201384"), /*#__PURE__*/React.createElement("span", null, "FAIL < 65"))), (passed.length || missed.length) && /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-2 gap-3 mb-4"
  }, passed.length ? /*#__PURE__*/React.createElement(PillList, {
    title: "Criteria Met",
    items: passed,
    accent: "green"
  }) : /*#__PURE__*/React.createElement("div", null), missed.length ? /*#__PURE__*/React.createElement(PillList, {
    title: "Criteria Missed",
    items: missed,
    accent: "red"
  }) : /*#__PURE__*/React.createElement("div", null)), /*#__PURE__*/React.createElement("button", {
    onClick: () => setSopOpen(v => !v),
    className: "flex items-center gap-2 text-sm text-gold-dark font-semibold hover:text-gold transition-all"
  }, sopOpen ? /*#__PURE__*/React.createElement(IcoChevD, {
    s: 14
  }) : /*#__PURE__*/React.createElement(IcoChevR, {
    s: 14
  }), " ", sopOpen ? 'Hide' : 'View', " SOP Criteria Table"), sopOpen && /*#__PURE__*/React.createElement("div", {
    className: "mt-3 border border-gray-200 rounded-xl overflow-hidden"
  }, /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-[160px_60px_1fr] bg-gray-50 border-b border-gray-200"
  }, ['Section', 'Max Pts', 'Criteria'].map(h => /*#__PURE__*/React.createElement("div", {
    key: h,
    className: "px-4 py-2 text-xs font-bold uppercase tracking-wider text-gray-400"
  }, h))), SOP_SECTIONS.map(([name, pts, desc]) => /*#__PURE__*/React.createElement("div", {
    key: name,
    className: "grid grid-cols-[160px_60px_1fr] border-b border-gray-100 last:border-0 hover:bg-gray-50"
  }, /*#__PURE__*/React.createElement("div", {
    className: "px-4 py-3 text-sm font-semibold text-gray-800"
  }, name), /*#__PURE__*/React.createElement("div", {
    className: "px-4 py-3 text-sm text-gold-dark font-bold"
  }, pts), /*#__PURE__*/React.createElement("div", {
    className: "px-4 py-3 text-sm text-gray-500"
  }, desc)))));
};
const SpeakerCard = ({
  sp
}) => {
  const [open, setOpen] = useState(false);
  const c = scoreColor(sp.score);
  return /*#__PURE__*/React.createElement("div", {
    className: "border border-gray-200 rounded-xl mb-3 overflow-hidden bg-white"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setOpen(v => !v),
    className: "w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-all"
  }, /*#__PURE__*/React.createElement("div", {
    className: "w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0",
    style: {
      background: `${c}18`,
      color: c
    }
  }, /*#__PURE__*/React.createElement(IcoUser, {
    s: 16
  })), /*#__PURE__*/React.createElement("div", {
    className: "flex-1 min-w-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-bold text-gray-900"
  }, sp.name || 'Speaker'), sp.role && /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 capitalize"
  }, String(sp.role).replace(/_/g, ' '))), /*#__PURE__*/React.createElement("div", {
    className: "text-right flex-shrink-0 mr-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-lg font-extrabold",
    style: {
      color: c
    }
  }, sp.score != null ? Number(sp.score).toFixed(1) : '—'), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400"
  }, "/10")), /*#__PURE__*/React.createElement("div", {
    className: "w-20 flex-shrink-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 text-right mb-1"
  }, sp.talk_time_pct || 0, "% talk"), /*#__PURE__*/React.createElement("div", {
    className: "h-1.5 bg-gray-200 rounded-full overflow-hidden"
  }, /*#__PURE__*/React.createElement("div", {
    className: "h-full rounded-full transition-all",
    style: {
      width: `${Math.min(sp.talk_time_pct || 0, 100)}%`,
      background: c
    }
  }))), open ? /*#__PURE__*/React.createElement(IcoChevD, {
    s: 13,
    c: "text-gray-400 flex-shrink-0 ml-1"
  }) : /*#__PURE__*/React.createElement(IcoChevR, {
    s: 13,
    c: "text-gray-400 flex-shrink-0 ml-1"
  })), open && /*#__PURE__*/React.createElement("div", {
    className: "px-4 pb-4 border-t border-gray-100"
  }, sp.summary && /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-gray-700 mt-3 mb-3 leading-relaxed italic"
  }, sp.summary), (sp.conformance_passed?.length || sp.conformance_missed?.length) && /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-2 gap-3"
  }, sp.conformance_passed?.length ? /*#__PURE__*/React.createElement(PillList, {
    title: "Conformance Met",
    items: sp.conformance_passed,
    accent: "green"
  }) : /*#__PURE__*/React.createElement("div", null), sp.conformance_missed?.length ? /*#__PURE__*/React.createElement(PillList, {
    title: "Conformance Missed",
    items: sp.conformance_missed,
    accent: "red"
  }) : /*#__PURE__*/React.createElement("div", null))));
};
const TabIndividual = ({
  f
}) => {
  const ind = f.individual_score;
  const color = scoreColor(ind);
  const confPassed = f.conformance_passed || [];
  const confMissed = f.conformance_missed || [];
  const speakers = f.speaker_scores || [];
  const chartData = [{
    name: 'Score',
    value: ind != null ? Number(ind) : 0
  }, {
    name: 'Remaining',
    value: ind != null ? 10 - Number(ind) : 10
  }];
  const COLORS = [color, '#e5e7eb'];
  return /*#__PURE__*/React.createElement("div", {
    className: "fade-in"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "Overall Score"), /*#__PURE__*/React.createElement("div", {
    className: "flex gap-6 mb-6"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bg-gray-50 border border-gray-200 rounded-2xl p-5 flex flex-col items-center justify-center w-44 flex-shrink-0"
  }, /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 140
  }, /*#__PURE__*/React.createElement(PieChart, null, /*#__PURE__*/React.createElement(Pie, {
    data: chartData,
    cx: "50%",
    cy: "50%",
    innerRadius: 45,
    outerRadius: 60,
    startAngle: 90,
    endAngle: -270,
    dataKey: "value",
    strokeWidth: 0
  }, chartData.map((_, i) => /*#__PURE__*/React.createElement(Cell, {
    key: i,
    fill: COLORS[i]
  }))))), /*#__PURE__*/React.createElement("div", {
    className: "text-2xl font-extrabold -mt-2",
    style: {
      color
    }
  }, ind != null ? Number(ind).toFixed(1) : '—', /*#__PURE__*/React.createElement("span", {
    className: "text-sm text-gray-400"
  }, "/10")), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 uppercase tracking-wider mt-1"
  }, "Individual")), /*#__PURE__*/React.createElement("div", {
    className: "flex-1"
  }, f.individual_summary && /*#__PURE__*/React.createElement("div", {
    className: "bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-800 leading-relaxed mb-4"
  }, f.individual_summary), (confPassed.length || confMissed.length) && /*#__PURE__*/React.createElement("div", {
    className: "grid grid-cols-2 gap-3"
  }, confPassed.length ? /*#__PURE__*/React.createElement(PillList, {
    title: "Conformance Met",
    items: confPassed,
    accent: "green"
  }) : /*#__PURE__*/React.createElement("div", null), confMissed.length ? /*#__PURE__*/React.createElement(PillList, {
    title: "Conformance Missed",
    items: confMissed,
    accent: "red"
  }) : /*#__PURE__*/React.createElement("div", null)))), speakers.length > 0 && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SectionLabel, {
    mt: true
  }, "Speaker Breakdown (", speakers.length, ")"), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 mb-3"
  }, "Click a speaker to expand their strengths and improvements"), speakers.map((sp, i) => /*#__PURE__*/React.createElement(SpeakerCard, {
    key: i,
    sp: sp
  }))), speakers.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "border border-dashed border-gray-200 rounded-xl p-6 text-center text-gray-400 text-sm"
  }, "Re-analyze the recording to get per-speaker breakdown"));
};
const TabRisks = ({
  f,
  risk
}) => {
  const risks = risk?.risks || [];
  const needsReview = risk?.needs_review;
  const tech = f.techstack_platform;
  return /*#__PURE__*/React.createElement("div", {
    className: "fade-in"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "Risk Report"), /*#__PURE__*/React.createElement("div", {
    className: "flex gap-6"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex-1"
  }, risks.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "bg-gold-light border border-gold-border rounded-xl p-5 text-gold-dark font-medium text-sm"
  }, "No risks identified in this recording.") : risks.map((r, i) => {
    const desc = typeof r === 'string' ? r : r.description || r.text || String(r);
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "bg-gold-light border border-gold-border rounded-xl p-4 mb-3 text-sm text-gray-900 leading-relaxed",
      style: {
        borderLeft: '3px solid #c9a84c'
      }
    }, desc);
  })), /*#__PURE__*/React.createElement("div", {
    className: "w-36 flex-shrink-0"
  }, /*#__PURE__*/React.createElement("div", {
    className: `rounded-xl p-4 text-center border ${needsReview ? 'bg-gray-900 border-gray-700' : 'bg-gold-light border-gold-border'}`
  }, needsReview ? /*#__PURE__*/React.createElement(IcoAlert, {
    s: 22,
    c: "mx-auto mb-2 text-white"
  }) : /*#__PURE__*/React.createElement(IcoShield, {
    s: 22,
    c: "mx-auto mb-2 text-gold-dark"
  }), /*#__PURE__*/React.createElement("div", {
    className: `text-xs font-bold uppercase tracking-wider ${needsReview ? 'text-white' : 'text-gold-dark'}`
  }, needsReview ? 'Needs Review' : 'All Clear')))), tech && (Array.isArray(tech) ? tech : [tech]).filter(Boolean).length > 0 && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SectionLabel, {
    mt: true
  }, "Tech Stack"), /*#__PURE__*/React.createElement("div", {
    className: "bg-gray-50 border border-gray-200 rounded-xl p-4"
  }, (Array.isArray(tech) ? tech : [tech]).filter(Boolean).map((t, i) => /*#__PURE__*/React.createElement(Chip, {
    key: i,
    label: t
  })))));
};
const TabRequirements = ({
  f
}) => {
  const reqs = f.strict_requirements || [];
  const [q, setQ] = useState('');
  const filtered = useMemo(() => reqs.filter(r => {
    const s = typeof r === 'string' ? r : r.title || r.description || String(r);
    return !q || s.toLowerCase().includes(q.toLowerCase());
  }), [reqs, q]);
  if (!reqs.length) return /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-gray-400 pt-4"
  }, "No requirements extracted for this recording.");
  return /*#__PURE__*/React.createElement("div", {
    className: "fade-in"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "Requirements ", /*#__PURE__*/React.createElement("span", {
    className: "font-normal text-gray-400 normal-case tracking-normal text-xs"
  }, "(", reqs.length, " items)")), /*#__PURE__*/React.createElement("div", {
    className: "relative mb-4"
  }, /*#__PURE__*/React.createElement(IcoSearch, {
    s: 14,
    c: "absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
  }), /*#__PURE__*/React.createElement("input", {
    value: q,
    onChange: e => setQ(e.target.value),
    placeholder: "Search requirements\u2026",
    className: "w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gold"
  })), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 mb-3"
  }, "Showing ", filtered.length, " of ", reqs.length), /*#__PURE__*/React.createElement("div", {
    className: "max-h-[520px] overflow-y-auto pr-1"
  }, filtered.map((r, i) => {
    const text = typeof r === 'string' ? r : r.title || r.description || String(r);
    const desc = typeof r === 'object' ? r.description : null;
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "flex gap-3 items-start py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 rounded px-1 transition-all"
    }, /*#__PURE__*/React.createElement("span", {
      className: "bg-gold-light text-gold-dark border border-gold-border rounded px-2 py-0.5 text-xs font-bold flex-shrink-0 mt-0.5"
    }, "REQ ", String(i + 1).padStart(2, '0')), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      className: "text-sm text-gray-900 leading-snug"
    }, text), desc && desc !== text && /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-gray-400 mt-1"
    }, desc)));
  })));
};
const TabTranscript = ({
  transcript,
  jobId
}) => {
  const sparkData = useMemo(() => {
    if (!transcript?.length) return [];
    const step = Math.max(1, Math.floor(transcript.length / 60));
    return transcript.filter((_, i) => i % step === 0).map(s => ({
      t: s.start?.slice(0, 5) || '',
      len: (s.text || '').length
    }));
  }, [transcript]);
  const full = (transcript || []).map(s => `[${(s.start || '').slice(0, 8)}] ${s.text || ''}`).join('\n');
  const dl = () => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([full], {
      type: 'text/plain'
    }));
    a.download = `${jobId}_transcript.txt`;
    a.click();
  };
  if (!transcript?.length) return /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-gray-400 pt-4"
  }, "No transcript available.");
  return /*#__PURE__*/React.createElement("div", {
    className: "fade-in"
  }, /*#__PURE__*/React.createElement(SectionLabel, null, "Activity"), /*#__PURE__*/React.createElement("div", {
    className: "mb-5 bg-gray-50 border border-gray-200 rounded-xl p-3"
  }, /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: 90
  }, /*#__PURE__*/React.createElement(AreaChart, {
    data: sparkData,
    margin: {
      top: 4,
      right: 0,
      left: 0,
      bottom: 0
    }
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: "g",
    x1: "0",
    y1: "0",
    x2: "0",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0%",
    stopColor: "#c9a84c",
    stopOpacity: 0.4
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "100%",
    stopColor: "#c9a84c",
    stopOpacity: 0
  }))), /*#__PURE__*/React.createElement(Area, {
    type: "monotone",
    dataKey: "len",
    stroke: "#c9a84c",
    fill: "url(#g)",
    strokeWidth: 1.5,
    dot: false
  }), /*#__PURE__*/React.createElement(XAxis, {
    dataKey: "t",
    tick: {
      fontSize: 9,
      fill: '#9ca3af'
    },
    axisLine: false,
    tickLine: false,
    interval: "preserveStartEnd"
  }), /*#__PURE__*/React.createElement(YAxis, {
    hide: true
  }), /*#__PURE__*/React.createElement(Tooltip, {
    contentStyle: {
      fontSize: 11,
      borderRadius: 6,
      border: '1px solid #e5e7eb'
    },
    labelStyle: {
      color: '#6b7280'
    },
    formatter: v => [v + ' chars', 'Length']
  })))), /*#__PURE__*/React.createElement(SectionLabel, null, "Segments \xB7 ", transcript.length), /*#__PURE__*/React.createElement("div", {
    className: "max-h-[480px] overflow-y-auto border border-gray-200 rounded-xl divide-y divide-gray-100"
  }, transcript.map((s, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "flex gap-3 px-4 py-3 hover:bg-gray-50 transition-all"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-xs font-mono text-gray-400 flex-shrink-0 mt-0.5 w-14"
  }, (s.start || '').slice(0, 8)), /*#__PURE__*/React.createElement("span", {
    className: "text-sm text-gray-800 leading-relaxed"
  }, s.text || '')))), /*#__PURE__*/React.createElement("button", {
    onClick: dl,
    className: "mt-4 flex items-center gap-1.5 text-xs font-semibold text-gold-dark border border-gold-border rounded-lg px-4 py-2 hover:bg-gold-light transition-all"
  }, /*#__PURE__*/React.createElement(IcoDl, {
    s: 13
  }), " Download Transcript (.txt)"));
};
const TABS = [{
  id: 'overview',
  label: 'Overview',
  Icon: IcoHome
}, {
  id: 'requirements',
  label: 'Requirements',
  Icon: IcoReq
}, {
  id: 'conformance',
  label: 'Conformance',
  Icon: IcoCheck
}, {
  id: 'individual',
  label: 'Individual',
  Icon: IcoUser
}, {
  id: 'risks',
  label: 'Risks',
  Icon: IcoShield
}, {
  id: 'transcript',
  label: 'Transcript',
  Icon: IcoFiles
}];
const AnalysisDashboard = ({
  rec,
  onBack,
  onUpdated
}) => {
  const [tab, setTab] = useState('overview');
  const [reanalyzing, setReanalyzing] = useState(false);
  const f = rec.extracted_fields || {};
  const risk = rec.risk_report || {};
  const risks = risk.risks || [];
  const reanalyze = async () => {
    setReanalyzing(true);
    try {
      const updated = await apiFetch(`/api/recordings/${rec.job_id}/reanalyze`, {
        method: 'POST'
      });
      onUpdated(updated);
    } catch (e) {
      alert('Re-analysis failed: ' + e);
    } finally {
      setReanalyzing(false);
    }
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "min-h-screen bg-white"
  }, /*#__PURE__*/React.createElement(TopBar, {
    rec: rec,
    onBack: onBack,
    onReanalyze: reanalyze,
    reanalyzing: reanalyzing
  }), /*#__PURE__*/React.createElement(ScoreStrip, {
    f: f,
    risks: risks,
    needsReview: risk.needs_review
  }), /*#__PURE__*/React.createElement("div", {
    className: "flex border-b border-gray-200 px-6 bg-white sticky top-[69px] z-10"
  }, TABS.map(({
    id,
    label,
    Icon
  }) => /*#__PURE__*/React.createElement("button", {
    key: id,
    onClick: () => setTab(id),
    className: `flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-all
              ${tab === id ? 'border-gold text-gold-dark' : 'border-transparent text-gray-500 hover:text-gray-800'}`
  }, /*#__PURE__*/React.createElement(Icon, {
    s: 13
  }), label))), /*#__PURE__*/React.createElement("div", {
    className: "px-6 py-6 max-w-5xl"
  }, tab === 'overview' && /*#__PURE__*/React.createElement(TabOverview, {
    f: f
  }), tab === 'conformance' && /*#__PURE__*/React.createElement(TabConformance, {
    f: f
  }), tab === 'individual' && /*#__PURE__*/React.createElement(TabIndividual, {
    f: f
  }), tab === 'risks' && /*#__PURE__*/React.createElement(TabRisks, {
    f: f,
    risk: risk
  }), tab === 'requirements' && /*#__PURE__*/React.createElement(TabRequirements, {
    f: f
  }), tab === 'transcript' && /*#__PURE__*/React.createElement(TabTranscript, {
    transcript: rec.transcript,
    jobId: rec.job_id
  })));
};

// ══════════════════════════════════════════════════════════════════════════
//  SECONDARY PAGES
// ══════════════════════════════════════════════════════════════════════════

const LivePage = () => /*#__PURE__*/React.createElement("div", {
  className: "flex-1 p-0"
}, /*#__PURE__*/React.createElement("iframe", {
  src: `${API}/static/live_transcription.html`,
  className: "w-full border-0",
  style: {
    height: 'calc(100vh - 0px)'
  },
  title: "Live Transcription"
}));
const CalendarPage = () => {
  const googleOk = true;
  return /*#__PURE__*/React.createElement("div", {
    className: "p-6 max-w-2xl fade-in"
  }, /*#__PURE__*/React.createElement("h1", {
    className: "text-2xl font-extrabold text-gray-900 mb-1"
  }, "Calendar Integration"), /*#__PURE__*/React.createElement("p", {
    className: "text-sm text-gray-400 mb-6"
  }, "Connect your calendar to automatically join and record meetings"), /*#__PURE__*/React.createElement("div", {
    className: "border border-gray-200 rounded-2xl overflow-hidden mb-6"
  }, [['Google Calendar', 'Auto-joins Zoom, Meet and Teams from Google Calendar', googleOk], ['Microsoft Outlook', 'Auto-joins Teams meetings from Outlook calendar', false]].map(([name, desc, ok]) => /*#__PURE__*/React.createElement("div", {
    key: name,
    className: "flex items-center justify-between px-5 py-4 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-all"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "font-semibold text-gray-900 text-sm"
  }, name), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-gray-400 mt-0.5"
  }, desc)), /*#__PURE__*/React.createElement(Badge, {
    label: ok ? 'Connected' : 'Not connected',
    type: ok ? 'green' : 'neutral'
  })))), /*#__PURE__*/React.createElement("details", {
    className: "border border-gray-200 rounded-xl mb-3"
  }, /*#__PURE__*/React.createElement("summary", {
    className: "px-5 py-3 cursor-pointer text-sm font-semibold text-gold-dark hover:bg-gold-light transition-all rounded-xl"
  }, "How to connect Google Calendar"), /*#__PURE__*/React.createElement("div", {
    className: "px-5 pb-4 text-sm text-gray-600 leading-relaxed pt-2"
  }, /*#__PURE__*/React.createElement("ol", {
    className: "list-decimal list-inside space-y-1"
  }, /*#__PURE__*/React.createElement("li", null, "Go to console.cloud.google.com \u2192 create a project"), /*#__PURE__*/React.createElement("li", null, "Enable ", /*#__PURE__*/React.createElement("strong", null, "Google Calendar API")), /*#__PURE__*/React.createElement("li", null, "Create OAuth 2.0 credentials (Desktop app) \u2192 download as ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, "credentials.json")), /*#__PURE__*/React.createElement("li", null, "Place ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, "credentials.json"), " in the project root"), /*#__PURE__*/React.createElement("li", null, "Set ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, "ENABLE_GOOGLE_CALENDAR=true"), " in ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, ".env")), /*#__PURE__*/React.createElement("li", null, "Run ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, "python -m app.main_agent"), " \u2014 browser opens for OAuth on first run")))), /*#__PURE__*/React.createElement("details", {
    className: "border border-gray-200 rounded-xl"
  }, /*#__PURE__*/React.createElement("summary", {
    className: "px-5 py-3 cursor-pointer text-sm font-semibold text-gold-dark hover:bg-gold-light transition-all rounded-xl"
  }, "How to connect Microsoft Outlook / Teams"), /*#__PURE__*/React.createElement("div", {
    className: "px-5 pb-4 text-sm text-gray-600 leading-relaxed pt-2"
  }, /*#__PURE__*/React.createElement("ol", {
    className: "list-decimal list-inside space-y-1"
  }, /*#__PURE__*/React.createElement("li", null, "Go to portal.azure.com \u2192 App registrations \u2192 New"), /*#__PURE__*/React.createElement("li", null, "Add delegated permission: ", /*#__PURE__*/React.createElement("strong", null, "Calendars.Read"), " (Microsoft Graph)"), /*#__PURE__*/React.createElement("li", null, "Set ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, "ENABLE_OUTLOOK_CALENDAR=true"), " and ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, "MICROSOFT_CLIENT_ID"), " in ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, ".env")), /*#__PURE__*/React.createElement("li", null, "Run ", /*#__PURE__*/React.createElement("code", {
    className: "bg-gray-100 px-1 rounded"
  }, "python -m app.main_agent"), " \u2014 device-code login appears once")))));
};
const RequirementsPage = () => /*#__PURE__*/React.createElement("div", {
  className: "p-6 max-w-2xl fade-in"
}, /*#__PURE__*/React.createElement("h1", {
  className: "text-2xl font-extrabold text-gray-900 mb-1"
}, "Requirements Extraction"), /*#__PURE__*/React.createElement("p", {
  className: "text-sm text-gray-400 mb-6"
}, "Open any recording and go to the ", /*#__PURE__*/React.createElement("strong", null, "Requirements"), " tab to see extracted requirements."), /*#__PURE__*/React.createElement("div", {
  className: "border border-gray-200 rounded-2xl p-8 text-center text-gray-400"
}, /*#__PURE__*/React.createElement(IcoReq, {
  s: 32,
  c: "mx-auto mb-3 opacity-30"
}), /*#__PURE__*/React.createElement("div", {
  className: "font-semibold text-gray-600 mb-1"
}, "No standalone report"), /*#__PURE__*/React.createElement("div", {
  className: "text-sm"
}, "Requirements are extracted automatically during recording processing and viewable per-recording in the analysis dashboard.")));

// ══════════════════════════════════════════════════════════════════════════
//  APP ROOT
// ══════════════════════════════════════════════════════════════════════════
const App = () => {
  const [page, setPage] = useState('home');
  const [selectedId, setSelectedId] = useState(null);
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [serverOk, setServerOk] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const loadRecordings = useCallback(() => {
    apiFetch('/api/recordings').then(data => {
      setRecordings(Array.isArray(data) ? data : []);
      setServerOk(true);
    }).catch(() => setServerOk(false)).finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    loadRecordings();
    apiFetch('/health').then(() => setServerOk(true)).catch(() => {});
  }, [loadRecordings]);
  const changePage = p => {
    setPage(p);
    setSelectedId(null);
  };
  const openRecording = id => setSelectedId(id);
  const closeRecording = () => setSelectedId(null);
  const handleProcessed = jobId => {
    loadRecordings();
    setTimeout(() => {
      setSelectedId(jobId);
      setPage('recordings');
    }, 400);
  };
  const handleUpdated = updated => {
    setRecordings(prev => prev.map(r => r.job_id === updated.job_id ? updated : r));
  };
  const selectedRec = selectedId ? recordings.find(r => r.job_id === selectedId) : null;
  if (selectedRec) {
    return /*#__PURE__*/React.createElement(AnalysisDashboard, {
      rec: selectedRec,
      onBack: closeRecording,
      onUpdated: handleUpdated
    });
  }
  const isFullWidth = page === 'live';
  const loadingSpinner = /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-center h-full text-gray-400 gap-2"
  }, /*#__PURE__*/React.createElement(IcoSpin, {
    s: 18
  }), "Loading\u2026");
  return /*#__PURE__*/React.createElement("div", {
    className: "flex h-screen overflow-hidden bg-white"
  }, /*#__PURE__*/React.createElement(Sidebar, {
    page: page,
    setPage: changePage,
    recordings: recordings,
    serverOk: serverOk,
    collapsed: !sidebarOpen,
    onToggle: () => setSidebarOpen(v => !v)
  }), /*#__PURE__*/React.createElement("div", {
    className: `flex-1 overflow-y-auto ${isFullWidth ? 'flex flex-col' : ''}`
  }, page === 'live' && /*#__PURE__*/React.createElement(LivePage, null), page === 'calendar' && /*#__PURE__*/React.createElement(CalendarPage, null), page === 'requirements' && /*#__PURE__*/React.createElement(RequirementsPage, null), page === 'home' && (loading ? loadingSpinner : /*#__PURE__*/React.createElement("div", {
    className: "flex gap-0 h-full"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex-1 min-w-0 overflow-y-auto"
  }, /*#__PURE__*/React.createElement(HomeDashboard, {
    recordings: recordings,
    onOpen: openRecording,
    onProcessed: handleProcessed,
    setPage: changePage,
    serverOk: serverOk
  })), /*#__PURE__*/React.createElement("div", {
    className: `${rightOpen ? 'w-72' : 'w-10'} flex-shrink-0 border-l border-gray-200 h-screen sticky top-0 flex flex-col overflow-hidden transition-all duration-200`,
    style: {
      minWidth: rightOpen ? '18rem' : '2.5rem'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: `flex border-b border-gray-200 py-2.5 flex-shrink-0 ${rightOpen ? 'justify-end px-3' : 'justify-center'}`
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setRightOpen(v => !v),
    title: rightOpen ? 'Hide panel' : 'Show panel',
    className: "p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gold-dark transition-all"
  }, /*#__PURE__*/React.createElement(IcoPanelRight, {
    s: 15
  }))), rightOpen && /*#__PURE__*/React.createElement("div", {
    className: "flex-1 overflow-y-auto p-4 space-y-3"
  }, /*#__PURE__*/React.createElement(Collapsible, {
    title: "Upload Recording",
    icon: /*#__PURE__*/React.createElement(IcoUpload, {
      s: 13
    }),
    defaultOpen: true
  }, /*#__PURE__*/React.createElement(UploadSection, {
    onProcessed: handleProcessed
  })), /*#__PURE__*/React.createElement(Collapsible, {
    title: "Join as Organizer",
    icon: /*#__PURE__*/React.createElement(IcoLive, {
      s: 13
    }),
    defaultOpen: true
  }, /*#__PURE__*/React.createElement(AgentPanel, null)), /*#__PURE__*/React.createElement(Collapsible, {
    title: "Upcoming Meetings",
    icon: /*#__PURE__*/React.createElement(IcoCal, {
      s: 13
    }),
    defaultOpen: true
  }, /*#__PURE__*/React.createElement(UpcomingMeetings, null)))))), page === 'recordings' && (loading ? loadingSpinner : /*#__PURE__*/React.createElement("div", {
    className: "flex gap-0 h-full"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex-1 min-w-0 overflow-y-auto"
  }, /*#__PURE__*/React.createElement(RecordingsPage, {
    recordings: recordings,
    onOpen: openRecording,
    onProcessed: handleProcessed
  })), /*#__PURE__*/React.createElement("div", {
    className: `${rightOpen ? 'w-72' : 'w-10'} flex-shrink-0 border-l border-gray-200 h-screen sticky top-0 flex flex-col overflow-hidden transition-all duration-200`,
    style: {
      minWidth: rightOpen ? '18rem' : '2.5rem'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: `flex border-b border-gray-200 py-2.5 flex-shrink-0 ${rightOpen ? 'justify-end px-3' : 'justify-center'}`
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setRightOpen(v => !v),
    title: rightOpen ? 'Hide panel' : 'Show panel',
    className: "p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gold-dark transition-all"
  }, /*#__PURE__*/React.createElement(IcoPanelRight, {
    s: 15
  }))), rightOpen && /*#__PURE__*/React.createElement("div", {
    className: "flex-1 overflow-y-auto p-4 space-y-3"
  }, /*#__PURE__*/React.createElement(Collapsible, {
    title: "Upload Recording",
    icon: /*#__PURE__*/React.createElement(IcoUpload, {
      s: 13
    }),
    defaultOpen: true
  }, /*#__PURE__*/React.createElement(UploadSection, {
    onProcessed: handleProcessed
  })), /*#__PURE__*/React.createElement(Collapsible, {
    title: "Join as Organizer",
    icon: /*#__PURE__*/React.createElement(IcoLive, {
      s: 13
    }),
    defaultOpen: false
  }, /*#__PURE__*/React.createElement(AgentPanel, null))))))));
};
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(App, null));
