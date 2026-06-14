import { Card } from "./ui/card";
import { Star } from "lucide-react";

const testimonials = [
  {
    name: "Алексей К.",
    role: "Предприниматель",
    avatar: "👨‍💼",
    rating: 5,
    text: "Использую VPN от Дяди Саши уже полгода. Скорость отличная, никаких обрывов. Особенно радует протокол Amnezia - работает даже там, где другие VPN блокируются.",
  },
  {
    name: "Мария С.",
    role: "Дизайнер",
    avatar: "👩‍🎨",
    rating: 5,
    text: "Наконец-то нашла VPN, который не тормозит при работе с большими файлами! Скачиваю дизайн-ресурсы на полной скорости. Рекомендую всем коллегам.",
  },
  {
    name: "Дмитрий П.",
    role: "IT-специалист",
    avatar: "👨‍💻",
    rating: 5,
    text: "Как технарь могу сказать - Amnezia WireGuard это действительно прорыв. Низкая задержка, высокая скорость, отличная обфускация. Цена более чем адекватная.",
  },
  {
    name: "Елена В.",
    role: "Маркетолог",
    avatar: "👩‍💼",
    rating: 5,
    text: "Пользуюсь для работы с соцсетями и аналитикой. Стабильное соединение, никаких проблем с доступом. Поддержка отвечает быстро и помогает решить любые вопросы.",
  },
  {
    name: "Игорь Т.",
    role: "Геймер",
    avatar: "🎮",
    rating: 5,
    text: "Играю на европейских серверах через VPN - пинг отличный, лагов нет. Раньше пробовал других провайдеров, но этот самый быстрый. Однозначно 5 звезд!",
  },
  {
    name: "Ольга Н.",
    role: "Блогер",
    avatar: "📱",
    rating: 5,
    text: "Путешествую часто, VPN всегда со мной. Работает стабильно в любой стране, на всех устройствах. Теперь могу спокойно вести соцсети из любой точки мира.",
  },
];

export function Testimonials() {
  return (
    <section className="px-6 py-20 md:py-32 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute right-0 top-1/3 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl"></div>
      
      <div className="max-w-7xl mx-auto relative">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            Отзывы наших клиентов
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Более 50,000 довольных пользователей по всему миру
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <Card 
              key={index}
              className="bg-slate-900/50 border-slate-800 backdrop-blur-sm p-6 hover:bg-slate-900/80 hover:border-blue-500/50 transition-all duration-300"
            >
              <div className="flex gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              
              <p className="text-slate-300 mb-6 leading-relaxed">
                "{testimonial.text}"
              </p>
              
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-2xl">
                  {testimonial.avatar}
                </div>
                <div>
                  <div className="text-white font-semibold">{testimonial.name}</div>
                  <div className="text-slate-400 text-sm">{testimonial.role}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
        
        <div className="text-center mt-12">
          <div className="inline-flex items-center gap-2 text-slate-400">
            <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
            <span className="text-xl">
              <span className="text-white font-bold">4.9</span> из 5 на основе 12,450+ отзывов
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
