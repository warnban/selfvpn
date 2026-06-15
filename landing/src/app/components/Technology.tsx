import { ImageWithFallback } from "./figma/ImageWithFallback";
import { CheckCircle2 } from "lucide-react";

const techPoints = [
  "Протокол Amnezia WireGuard — стабильное соединение",
  "Оптимизация канала под реальные сети",
  "Защита от утечек DNS и WebRTC",
  "Автоотключение при разрыве соединения",
  "Мультиплатформенность: Windows, macOS, iOS, Android, Linux",
];

export function Technology() {
  return (
    <section className="px-6 py-20 md:py-32 relative overflow-hidden">
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl"></div>
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl"></div>
      
      <div className="max-w-7xl mx-auto relative">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="order-2 lg:order-1 relative">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/30 to-purple-600/30 rounded-3xl blur-2xl"></div>
            <ImageWithFallback 
              src="https://images.unsplash.com/photo-1758073519996-6d3c63b4922c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMHRlY2hub2xvZ3klMjBibHVlJTIwZGlnaXRhbHxlbnwxfHx8fDE3ODE0MDY3ODR8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
              alt="Технологии соединения"
              className="relative rounded-3xl shadow-2xl border border-slate-700/50"
            />
          </div>
          
          <div className="order-1 lg:order-2 space-y-8">
            <div className="space-y-4">
              <div className="inline-block px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-300 text-sm font-medium">
                Технологии
              </div>
              <h2 className="text-4xl md:text-5xl font-bold text-white">
                Надёжный канал с Amnezia
              </h2>
              <p className="text-xl text-slate-400">
                Используем протокол Amnezia WireGuard для стабильного и быстрого персонального интернет-канала.
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
          </div>
        </div>
      </div>
    </section>
  );
}
