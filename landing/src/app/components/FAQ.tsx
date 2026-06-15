import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";

const faqs = [
  {
    question: "Что такое протокол Amnezia и чем он отличается?",
    answer: "Amnezia — развитие WireGuard с оптимизацией для стабильной работы в реальных сетях. Соединение остаётся быстрым и надёжным при любой нагрузке."
  },
  {
    question: "Можно ли использовать на нескольких устройствах?",
    answer: "Да! Подключайте телефон, ноутбук, планшет и другие устройства. Сервис работает на Windows, macOS, iOS, Android и Linux."
  },
  {
    question: "Как работает бесплатный пробный период?",
    answer: "Вы получаете полный доступ ко всем функциям на 2 дня бесплатно. Не требуется привязка банковской карты."
  },
  {
    question: "Насколько безопасен сервис?",
    answer: "Мы придерживаемся политики no-logs, не храним данные о вашей активности и используем защиту от утечек DNS и WebRTC."
  },
  {
    question: "Какая скорость подключения?",
    answer: "Канал поддерживает скорость до 1 Гбит/с. Реальная скорость зависит от вашего интернет-подключения."
  },
  {
    question: "Можно ли вернуть деньги, если не понравится?",
    answer: "Да, обратитесь в поддержку — разберёмся с возвратом при технических сбоях или ошибочном списании."
  },
  {
    question: "Какие способы оплаты вы принимаете?",
    answer: "Банковские карты РФ и Telegram Stars. Оплата через личный кабинет или бота @anfikvpnbot."
  },
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
            Ответы на популярные вопросы о сервисе
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
            href="/about#support" 
            className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
          >
            Свяжитесь с поддержкой →
          </a>
        </div>
      </div>
    </section>
  );
}
