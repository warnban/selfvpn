import { useState } from "react";
import { Shield, Zap, Lock, Eye, Globe, Clock, ChevronDown, Star, Send, CreditCard, Users, Copy, Check } from "lucide-react";

const LIME = "#b8ff00";

function Nav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[rgba(184,255,0,0.08)] bg-[#070707]/90 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span style={{ fontFamily: "'Barlow Condensed', sans-serif" }} className="text-2xl font-black tracking-tight text-white">
            VPN<span style={{ color: LIME }}>.</span>ДЯДИ<span style={{ color: LIME }}>.</span>САНИ
          </span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm text-[#666]" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          <a href="#features" className="hover:text-white transition-colors">протокол</a>
          <a href="#pricing" className="hover:text-white transition-colors">тарифы</a>
          <a href="#faq" className="hover:text-white transition-colors">faq</a>
        </div>
        <a
          href="#pricing"
          style={{ backgroundColor: LIME, fontFamily: "'Barlow Condensed', sans-serif", color: "#070707" }}
          className="px-5 py-2 text-sm font-bold tracking-wide uppercase transition-opacity hover:opacity-80"
        >
          Подключить
        </a>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <section className="pt-16 min-h-screen flex flex-col justify-center relative overflow-hidden">
      {/* Grid background */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: "linear-gradient(rgba(184,255,0,1) 1px, transparent 1px), linear-gradient(90deg, rgba(184,255,0,1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />
      {/* Glow */}
      <div
        className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full opacity-10 blur-[120px]"
        style={{ backgroundColor: LIME }}
      />

      <div className="max-w-6xl mx-auto px-6 py-20 relative">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left */}
          <div>
            <div
              className="inline-flex items-center gap-2 px-3 py-1 mb-8 border text-xs tracking-widest uppercase"
              style={{ borderColor: "rgba(184,255,0,0.3)", color: LIME, fontFamily: "'JetBrains Mono', monospace" }}
            >
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: LIME }} />
              Протокол Amnezia — невидим для DPI
            </div>

            <h1
              style={{ fontFamily: "'Barlow Condensed', sans-serif", lineHeight: 0.9 }}
              className="text-[80px] md:text-[110px] font-black uppercase text-white mb-6 tracking-tight"
            >
              VPN<br />
              <span style={{ color: LIME }}>от Дяди</span><br />
              Сани
            </h1>

            <p className="text-[#888] text-lg mb-10 max-w-md" style={{ fontFamily: "'Manrope', sans-serif" }}>
              Работает там, где другие уже сдались. Без логов, без слежки, без блокировок. Личный VPN от живого человека.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-10">
              <a
                href="#pricing"
                style={{ backgroundColor: LIME, fontFamily: "'Barlow Condensed', sans-serif", color: "#070707" }}
                className="px-8 py-4 text-xl font-black uppercase tracking-wide text-center hover:opacity-90 transition-opacity"
              >
                2 дня бесплатно →
              </a>
              <a
                href="#features"
                style={{ borderColor: "rgba(255,255,255,0.15)", fontFamily: "'Barlow Condensed', sans-serif" }}
                className="px-8 py-4 text-xl font-bold uppercase tracking-wide border text-white text-center hover:border-white/40 transition-colors"
              >
                Как это работает
              </a>
            </div>

            <div
              className="flex flex-wrap gap-x-6 gap-y-3 text-sm"
              style={{ fontFamily: "'JetBrains Mono', monospace", color: "#555" }}
            >
              <span style={{ color: LIME }}>✓</span>&nbsp;<span className="text-[#aaa]">2 дня бесплатно</span>
              <span style={{ color: LIME }}>✓</span>&nbsp;<span className="text-[#aaa]">10 ₽/сутки</span>
              <span style={{ color: LIME }}>✓</span>&nbsp;<span className="text-[#aaa]">Оплата картой или Telegram ⭐</span>
              <span style={{ color: LIME }}>✓</span>&nbsp;<span className="text-[#aaa]">Без привязки карты</span>
            </div>
          </div>

          {/* Right — terminal card */}
          <div className="lg:block hidden">
            <div
              className="border rounded-sm overflow-hidden"
              style={{ borderColor: "rgba(184,255,0,0.2)", backgroundColor: "#0a0a0a" }}
            >
              <div className="flex items-center gap-2 px-4 py-3 border-b" style={{ borderColor: "rgba(184,255,0,0.1)" }}>
                <span className="w-3 h-3 rounded-full bg-red-500/70" />
                <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: `${LIME}99` }} />
                <span className="ml-2 text-xs text-[#444]" style={{ fontFamily: "'JetBrains Mono', monospace" }}>anfikvpnbot</span>
              </div>
              <div className="p-6 space-y-3" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "13px" }}>
                <div className="text-[#444]">$ ping status.vpn</div>
                <div style={{ color: LIME }}>✓ Сервер онлайн — 99.9% uptime</div>
                <div className="text-[#444]">$ check protocol</div>
                <div style={{ color: LIME }}>✓ AmneziaWG активен</div>
                <div className="text-[#444]">$ run speed-test</div>
                <div style={{ color: LIME }}>↑ 940 Мбит/с  ↓ 980 Мбит/с</div>
                <div className="text-[#444]">$ check-logs</div>
                <div style={{ color: LIME }}>✓ Логов не найдено. Вообще.</div>
                <div className="text-[#444]">$ detect-ip-leak</div>
                <div style={{ color: LIME }}>✓ Утечек не обнаружено</div>
                <div className="flex items-center gap-1 text-[#444]">
                  <span>$</span>
                  <span className="w-2 h-4 animate-pulse ml-1" style={{ backgroundColor: LIME }} />
                </div>
              </div>
              <div
                className="grid grid-cols-3 border-t divide-x text-center"
                style={{ borderColor: "rgba(184,255,0,0.1)", divideColor: "rgba(184,255,0,0.1)" }}
              >
                {[["10 ₽", "в сутки"], ["2 дня", "бесплатно"], ["∞", "трафик"]].map(([v, l]) => (
                  <div key={l} className="py-4">
                    <div className="text-xl font-bold" style={{ color: LIME, fontFamily: "'Barlow Condensed', sans-serif" }}>{v}</div>
                    <div className="text-xs text-[#555] mt-0.5" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{l}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const features = [
  {
    icon: Shield,
    title: "Amnezia WG",
    desc: "Трафик выглядит как обычный HTTPS. DPI-системы провайдера не видят VPN. Работает даже там, где другие уже заблокированы.",
  },
  {
    icon: Zap,
    title: "Скорость до 1 Гбит/с",
    desc: "Выделенный канал без ограничений по скорости. Стриминг, торренты, звонки — без тормозов.",
  },
  {
    icon: Eye,
    title: "Ноль логов",
    desc: "Не ведём никаких журналов активности. Даже если очень попросят — нечего отдать.",
  },
  {
    icon: Globe,
    title: "Все устройства",
    desc: "iOS, Android, Windows, macOS, Linux. Один аккаунт — подключай сколько угодно устройств.",
  },
  {
    icon: Lock,
    title: "AES-256 + ChaCha20",
    desc: "Военное шифрование. Ключи генерируются на вашем устройстве — мы их не видим.",
  },
  {
    icon: Clock,
    title: "Поддержка живая",
    desc: "Не бот, не скрипт — живой Саня отвечает в Telegram. Обычно в течение часа.",
  },
];

function Features() {
  return (
    <section id="features" className="py-24 relative">
      <div className="max-w-6xl mx-auto px-6">
        <div className="mb-16">
          <div
            className="text-xs tracking-widest uppercase mb-4"
            style={{ color: LIME, fontFamily: "'JetBrains Mono', monospace" }}
          >
            01 / почему это работает
          </div>
          <h2
            style={{ fontFamily: "'Barlow Condensed', sans-serif", lineHeight: 0.95 }}
            className="text-6xl md:text-8xl font-black uppercase text-white"
          >
            Невидимый<br />
            <span style={{ color: LIME }}>протокол</span>
          </h2>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-px" style={{ backgroundColor: "rgba(184,255,0,0.08)" }}>
          {features.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="p-8 group hover:bg-[#0f0f0f] transition-colors"
              style={{ backgroundColor: "#070707" }}
            >
              <div
                className="w-10 h-10 flex items-center justify-center mb-6 border group-hover:border-[rgba(184,255,0,0.5)] transition-colors"
                style={{ borderColor: "rgba(184,255,0,0.2)" }}
              >
                <Icon className="w-5 h-5" style={{ color: LIME }} />
              </div>
              <h3
                style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
                className="text-2xl font-bold uppercase text-white mb-3 tracking-wide"
              >
                {title}
              </h3>
              <p className="text-[#666] text-sm leading-relaxed" style={{ fontFamily: "'Manrope', sans-serif" }}>
                {desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText("anfikvpnbot");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="pricing" className="py-24">
      <div className="max-w-6xl mx-auto px-6">
        <div className="mb-16">
          <div
            className="text-xs tracking-widest uppercase mb-4"
            style={{ color: LIME, fontFamily: "'JetBrains Mono', monospace" }}
          >
            02 / тарифы
          </div>
          <h2
            style={{ fontFamily: "'Barlow Condensed', sans-serif", lineHeight: 0.95 }}
            className="text-6xl md:text-8xl font-black uppercase text-white"
          >
            Одна цена.<br />
            <span style={{ color: LIME }}>Честно.</span>
          </h2>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Main plan */}
          <div
            className="border p-10 relative"
            style={{ borderColor: LIME, backgroundColor: "#0a0a0a" }}
          >
            <div
              className="absolute top-0 right-0 px-4 py-2 text-xs font-bold uppercase tracking-widest"
              style={{ backgroundColor: LIME, color: "#070707", fontFamily: "'JetBrains Mono', monospace" }}
            >
              Единственный тариф
            </div>

            <div className="mt-4 mb-8">
              <div
                style={{ fontFamily: "'Barlow Condensed', sans-serif", color: LIME, lineHeight: 1 }}
                className="text-[80px] font-black"
              >
                10 ₽
              </div>
              <div className="text-[#666] text-lg -mt-1" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                в сутки — и ничего лишнего
              </div>
            </div>

            <div className="space-y-3 mb-10">
              {[
                "Безлимитный трафик",
                "Скорость до 1 Гбит/с",
                "Все устройства без ограничений",
                "Протокол AmneziaWG",
                "Шифрование AES-256 + ChaCha20",
                "Ноль логов",
                "Живая поддержка в Telegram",
              ].map((f) => (
                <div key={f} className="flex items-center gap-3" style={{ fontFamily: "'Manrope', sans-serif" }}>
                  <Check className="w-4 h-4 flex-shrink-0" style={{ color: LIME }} />
                  <span className="text-[#ccc] text-sm">{f}</span>
                </div>
              ))}
            </div>

            <div
              className="border-t pt-6 mb-8 grid grid-cols-2 gap-4"
              style={{ borderColor: "rgba(255,255,255,0.06)" }}
            >
              <div>
                <div
                  className="text-xs uppercase tracking-widest mb-2"
                  style={{ color: "#555", fontFamily: "'JetBrains Mono', monospace" }}
                >
                  Пробный период
                </div>
                <div className="text-white font-semibold text-lg" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
                  2 дня бесплатно
                </div>
              </div>
              <div>
                <div
                  className="text-xs uppercase tracking-widest mb-2"
                  style={{ color: "#555", fontFamily: "'JetBrains Mono', monospace" }}
                >
                  Оплата
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="flex items-center gap-1 text-sm text-[#aaa]" style={{ fontFamily: "'Manrope', sans-serif" }}>
                    <CreditCard className="w-3.5 h-3.5" style={{ color: LIME }} />
                    Карта РФ
                  </div>
                  <div className="flex items-center gap-1 text-sm text-[#aaa]" style={{ fontFamily: "'Manrope', sans-serif" }}>
                    <Send className="w-3.5 h-3.5" style={{ color: LIME }} />
                    Telegram ⭐
                  </div>
                </div>
              </div>
            </div>

            <a
              href="https://t.me/anfikvpnbot"
              target="_blank"
              rel="noopener noreferrer"
              style={{ backgroundColor: LIME, fontFamily: "'Barlow Condensed', sans-serif", color: "#070707" }}
              className="block w-full py-4 text-xl font-black uppercase tracking-wide text-center hover:opacity-90 transition-opacity"
            >
              Попробовать 2 дня бесплатно →
            </a>
            <p
              className="text-center mt-3 text-xs"
              style={{ color: "#444", fontFamily: "'JetBrains Mono', monospace" }}
            >
              без привязки карты · отмена в любой момент
            </p>
          </div>

          {/* Referral block */}
          <div className="space-y-6">
            <div
              className="border p-8"
              style={{ borderColor: "rgba(184,255,0,0.2)", backgroundColor: "#0a0a0a" }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div
                  className="w-10 h-10 flex items-center justify-center border"
                  style={{ borderColor: "rgba(184,255,0,0.3)" }}
                >
                  <Users className="w-5 h-5" style={{ color: LIME }} />
                </div>
                <div>
                  <h3
                    style={{ fontFamily: "'Barlow Condensed', sans-serif" }}
                    className="text-2xl font-bold uppercase text-white tracking-wide"
                  >
                    Реферальная программа
                  </h3>
                  <p className="text-xs text-[#555]" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                    зарабатывай с каждого друга
                  </p>
                </div>
              </div>

              <div
                className="text-center py-6 mb-6 border"
                style={{ borderColor: "rgba(184,255,0,0.15)", backgroundColor: "rgba(184,255,0,0.03)" }}
              >
                <div
                  style={{ fontFamily: "'Barlow Condensed', sans-serif", color: LIME, lineHeight: 1 }}
                  className="text-7xl font-black"
                >
                  30 ₽
                </div>
                <div className="text-[#666] mt-2 text-sm" style={{ fontFamily: "'Manrope', sans-serif" }}>
                  за каждого приглашённого друга
                </div>
              </div>

              <div className="space-y-3" style={{ fontFamily: "'Manrope', sans-serif" }}>
                {[
                  "Делишься своей реферальной ссылкой",
                  "Друг подключается и начинает платить",
                  "Ты получаешь 30 ₽ на баланс",
                  "Деньги не сгорают, можно вывести",
                ].map((s, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm text-[#888]">
                    <span
                      className="flex-shrink-0 w-5 h-5 text-xs flex items-center justify-center border mt-0.5"
                      style={{ borderColor: "rgba(184,255,0,0.25)", color: LIME, fontFamily: "'JetBrains Mono', monospace" }}
                    >
                      {i + 1}
                    </span>
                    {s}
                  </div>
                ))}
              </div>
            </div>

            {/* Telegram CTA */}
            <div
              className="border p-8 flex items-center gap-6"
              style={{ borderColor: "rgba(184,255,0,0.15)", backgroundColor: "#0a0a0a" }}
            >
              <div
                className="w-14 h-14 flex items-center justify-center flex-shrink-0 border"
                style={{ borderColor: "rgba(184,255,0,0.2)" }}
              >
                <Send className="w-6 h-6" style={{ color: LIME }} />
              </div>
              <div className="flex-1">
                <div className="text-white font-bold mb-1" style={{ fontFamily: "'Barlow Condensed', sans-serif", fontSize: "20px" }}>
                  Подключаемся в Telegram
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-2 text-sm transition-colors"
                  style={{ color: "#666", fontFamily: "'JetBrains Mono', monospace" }}
                >
                  <span>@anfikvpnbot</span>
                  {copied
                    ? <Check className="w-3.5 h-3.5" style={{ color: LIME }} />
                    : <Copy className="w-3.5 h-3.5 hover:text-white" />
                  }
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const testimonials = [
  {
    name: "Алексей М.",
    role: "разработчик",
    text: "Пробовал кучу VPN — блокировались один за другим. Этот работает уже 4 месяца без единого сбоя. Amnezia реально не видно.",
    stars: 5,
  },
  {
    name: "Марина К.",
    role: "дизайнер",
    text: "Саня помог настроить на всех устройствах сам. Такого сервиса я не встречала — живой человек, отвечает быстро.",
    stars: 5,
  },
  {
    name: "Дмитрий В.",
    role: "предприниматель",
    text: "10 рублей в день — это честная цена. Скорость на уровне, потоковое видео летит. Рекомендую коллегам.",
    stars: 5,
  },
];

function Testimonials() {
  return (
    <section className="py-24 border-t" style={{ borderColor: "rgba(184,255,0,0.08)" }}>
      <div className="max-w-6xl mx-auto px-6">
        <div className="mb-16">
          <div
            className="text-xs tracking-widest uppercase mb-4"
            style={{ color: LIME, fontFamily: "'JetBrains Mono', monospace" }}
          >
            03 / отзывы
          </div>
          <h2
            style={{ fontFamily: "'Barlow Condensed', sans-serif", lineHeight: 0.95 }}
            className="text-6xl md:text-7xl font-black uppercase text-white"
          >
            Говорят<br />
            <span style={{ color: LIME }}>клиенты</span>
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-px" style={{ backgroundColor: "rgba(184,255,0,0.08)" }}>
          {testimonials.map(({ name, role, text, stars }) => (
            <div key={name} className="p-8" style={{ backgroundColor: "#070707" }}>
              <div className="flex gap-0.5 mb-6">
                {Array.from({ length: stars }).map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-current" style={{ color: LIME }} />
                ))}
              </div>
              <p
                className="text-[#aaa] text-sm leading-relaxed mb-8"
                style={{ fontFamily: "'Manrope', sans-serif" }}
              >
                &ldquo;{text}&rdquo;
              </p>
              <div>
                <div className="text-white font-semibold text-sm" style={{ fontFamily: "'Manrope', sans-serif" }}>
                  {name}
                </div>
                <div className="text-xs mt-0.5" style={{ color: "#444", fontFamily: "'JetBrains Mono', monospace" }}>
                  {role}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const faqs = [
  {
    q: "Почему Amnezia лучше обычного WireGuard?",
    a: "Обычный WireGuard имеет характерный отпечаток пакетов, который легко обнаруживается DPI-системами (глубокая инспекция трафика). AmneziaWG рандомизирует этот отпечаток — трафик выглядит как обычные зашифрованные данные. Провайдер не может понять, что это VPN.",
  },
  {
    q: "Как именно оплатить через Telegram Stars?",
    a: "Напишите в @anfikvpnbot — Саня пришлёт ссылку на оплату через Telegram. Stars — официальная валюта Telegram, ничего дополнительно устанавливать не надо.",
  },
  {
    q: "Сколько устройств можно подключить?",
    a: "Ограничений нет. Телефон, ноутбук, планшет, роутер — подключайте всё, что нужно.",
  },
  {
    q: "Как работает реферальная программа?",
    a: "После регистрации вы получаете личную ссылку. Каждый, кто подключится по ней и начнёт платить, приносит вам 30 ₽ на баланс. Накопленное можно использовать для оплаты своего VPN или вывести.",
  },
  {
    q: "Что будет после 2 бесплатных дней?",
    a: "Ничего автоматически не спишется — подключение просто остановится. Вы сами решаете, пополнить баланс или нет. Никаких скрытых списаний.",
  },
  {
    q: "Логи правда не ведёте?",
    a: "Правда. Система устроена так, что даже при большом желании нам нечего было бы передать. Нет базы данных активности, нет истории соединений.",
  },
];

function FAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" className="py-24 border-t" style={{ borderColor: "rgba(184,255,0,0.08)" }}>
      <div className="max-w-6xl mx-auto px-6">
        <div className="mb-16">
          <div
            className="text-xs tracking-widest uppercase mb-4"
            style={{ color: LIME, fontFamily: "'JetBrains Mono', monospace" }}
          >
            04 / вопросы
          </div>
          <h2
            style={{ fontFamily: "'Barlow Condensed', sans-serif", lineHeight: 0.95 }}
            className="text-6xl md:text-7xl font-black uppercase text-white"
          >
            FAQ
          </h2>
        </div>

        <div className="divide-y" style={{ borderColor: "rgba(184,255,0,0.08)" }}>
          {faqs.map(({ q, a }, i) => (
            <div key={i}>
              <button
                className="w-full flex items-center justify-between gap-6 py-6 text-left group"
                onClick={() => setOpen(open === i ? null : i)}
              >
                <span
                  className="text-white font-semibold group-hover:text-[#b8ff00] transition-colors"
                  style={{ fontFamily: "'Manrope', sans-serif" }}
                >
                  {q}
                </span>
                <ChevronDown
                  className="w-5 h-5 flex-shrink-0 transition-transform"
                  style={{ color: LIME, transform: open === i ? "rotate(180deg)" : "rotate(0)" }}
                />
              </button>
              {open === i && (
                <div
                  className="pb-6 text-sm leading-relaxed"
                  style={{ color: "#777", fontFamily: "'Manrope', sans-serif" }}
                >
                  {a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer
      className="border-t py-12"
      style={{ borderColor: "rgba(184,255,0,0.08)" }}
    >
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <span style={{ fontFamily: "'Barlow Condensed', sans-serif" }} className="text-xl font-black tracking-tight text-white">
          VPN<span style={{ color: LIME }}>.</span>ДЯДИ<span style={{ color: LIME }}>.</span>САНИ
        </span>

        <div
          className="text-xs text-center"
          style={{ color: "#444", fontFamily: "'JetBrains Mono', monospace" }}
        >
          10 ₽/сутки · 2 дня бесплатно · Amnezia WG · Без логов
        </div>

        <a
          href="https://t.me/anfikvpnbot"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-sm transition-colors hover:opacity-70"
          style={{ color: LIME, fontFamily: "'JetBrains Mono', monospace" }}
        >
          <Send className="w-4 h-4" />
          @anfikvpnbot
        </a>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <div style={{ backgroundColor: "#070707", fontFamily: "'Manrope', sans-serif" }} className="min-h-screen">
      <Nav />
      <Hero />
      <Features />
      <Pricing />
      <Testimonials />
      <FAQ />
      <Footer />
    </div>
  );
}
