import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";

const faqs = [
  {
    question: "Что такое протокол Amnezia и чем он отличается?",
    answer: "Amnezia - это модифицированная версия WireGuard с функцией обфускации трафика. Он маскирует VPN-соединение под обычный HTTPS-трафик, что делает его невидимым для систем глубокой проверки пакетов (DPI) и защищает от блокировок."
  },
  {
    question: "Можно ли использовать на нескольких устройствах?",
    answer: "Да! В зависимости от тарифа вы можете подключить от 5 до неограниченного количества устройств. VPN работает на всех популярных платформах: Windows, macOS, iOS, Android и Linux."
  },
  {
    question: "Как работает бесплатный пробный период?",
    answer: "Вы получаете полный доступ ко всем функциям VPN на 7 дней абсолютно бесплатно. Не требуется привязка банковской карты. После окончания пробного периода вы можете выбрать подходящий тариф."
  },
  {
    question: "Насколько безопасен VPN от Дяди Саши?",
    answer: "Мы используем военное шифрование AES-256, строгую политику no-logs (не храним данные о вашей активности), защиту от утечек DNS и WebRTC, а также Kill Switch для автоматической защиты при разрыве соединения."
  },
  {
    question: "Какая скорость подключения?",
    answer: "Наши серверы поддерживают скорость до 10 Гбит/с. Реальная скорость зависит от вашего интернет-подключения и удаленности от выбранного сервера. В большинстве случаев потеря скорости минимальна - 5-10%."
  },
  {
    question: "Можно ли вернуть деньги, если не понравится?",
    answer: "Да, мы предоставляем гарантию возврата денег в течение 30 дней. Если VPN вам не подойдет, просто напишите в поддержку и мы вернем полную стоимость без лишних вопросов."
  },
  {
    question: "Какие способы оплаты вы принимаете?",
    answer: "Мы принимаем банковские карты РФ (Visa, Mastercard, МИР), криптовалюту (Bitcoin, Ethereum, USDT), ЮMoney, QIWI. Для максимальной анонимности рекомендуем оплату криптовалютой."
  },
  {
    question: "Работает ли VPN в Китае и других странах с блокировками?",
    answer: "Да! Благодаря протоколу Amnezia наш VPN успешно работает даже в странах с жесткой интернет-цензурой, включая Китай, Иран, ОАЭ и другие. Обфускация трафика делает VPN-соединение неотличимым от обычного HTTPS."
  }
];

export function FAQ() {
  return (
    <section className="px-6 py-20 md:py-32 relative">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            Частые вопросы
          </h2>
          <p className="text-xl text-slate-400">
            Ответы на популярные вопросы о нашем VPN-сервисе
          </p>
        </div>
        
        <Accordion type="single" collapsible className="space-y-4">
          {faqs.map((faq, index) => (
            <AccordionItem 
              key={index} 
              value={`item-${index}`}
              className="bg-slate-900/50 border-slate-800 backdrop-blur-sm rounded-xl px-6 hover:bg-slate-900/80 transition-colors"
            >
              <AccordionTrigger className="text-left text-white hover:text-blue-400 py-6">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="text-slate-400 pb-6 leading-relaxed">
                {faq.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
        
        <div className="mt-12 text-center">
          <p className="text-slate-400 mb-4">Не нашли ответ на свой вопрос?</p>
          <a 
            href="#" 
            className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
          >
            Свяжитесь с нашей поддержкой 24/7 →
          </a>
        </div>
      </div>
    </section>
  );
}
