import { ImageWithFallback } from "./figma/ImageWithFallback";
import { CheckCircle2 } from "lucide-react";

const techPoints = [
  "Протокол Amnezia WireGuard - невидимый для блокировок",
  "Обфускация трафика под обычный HTTPS",
  "Динамическая смена портов и IP-адресов",
  "Защита от утечек DNS и WebRTC",
  "Kill Switch - автоматическое отключение при разрыве VPN",
  "Мультиплатформенность: Windows, macOS, iOS, Android, Linux",
];

export function Technology() {
  return (
    <section className="px-6 py-20 md:py-32 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl"></div>
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl"></div>
      
      <div className="max-w-7xl mx-auto relative">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left - Image */}
          <div className="order-2 lg:order-1 relative">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/30 to-purple-600/30 rounded-3xl blur-2xl"></div>
            <ImageWithFallback 
              src="https://images.unsplash.com/photo-1758073519996-6d3c63b4922c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMHRlY2hub2xvZ3klMjBibHVlJTIwZGlnaXRhbHxlbnwxfHx8fDE3ODE0MDY3ODR8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
              alt="Advanced technology"
              className="relative rounded-3xl shadow-2xl border border-slate-700/50"
            />
          </div>
          
          {/* Right - Content */}
          <div className="order-1 lg:order-2 space-y-8">
            <div className="space-y-4">
              <div className="inline-block px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-300 text-sm font-medium">
                Технологии будущего
              </div>
              <h2 className="text-4xl md:text-5xl font-bold text-white">
                Непробиваемая защита с Amnezia
              </h2>
              <p className="text-xl text-slate-400">
                Используем передовой протокол Amnezia WireGuard, который делает ваше подключение невидимым для систем глубокой проверки пакетов (DPI).
              </p>
            </div>
            
            <div className="space-y-4">
              {techPoints.map((point, index) => (
                <div key={index} className="flex items-start gap-3 group">
                  <div className="flex-shrink-0 w-6 h-6 mt-0.5">
                    <CheckCircle2 className="w-6 h-6 text-blue-400 group-hover:text-blue-300 transition-colors" />
                  </div>
                  <span className="text-slate-300 group-hover:text-white transition-colors">
                    {point}
                  </span>
                </div>
              ))}
            </div>
            
            <div className="pt-6">
              <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30 rounded-2xl p-6">
                <div className="flex items-center gap-4">
                  <div className="text-4xl">🚀</div>
                  <div>
                    <div className="text-white font-semibold mb-1">
                      Скорость до 10 Гбит/с
                    </div>
                    <div className="text-slate-400 text-sm">
                      Наши серверы оптимизированы для максимальной производительности
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
