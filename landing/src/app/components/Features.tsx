import { Shield, Zap, Globe, Lock, Server, Eye } from "lucide-react";
import { Card } from "./ui/card";

const features = [
  {
    icon: Shield,
    title: "Протокол Amnezia",
    description: "Современный протокол AmneziaWG для стабильного персонального канала в любых сетевых условиях.",
  },
  {
    icon: Zap,
    title: "Максимальная скорость",
    description: "Скорость до 1 Гбит/с. Смотрите видео и работайте с файлами без задержек.",
  },
  {
    icon: Globe,
    title: "Все устройства",
    description: "Телефон, ноутбук, планшет — подключайте всё, что нужно, с одного аккаунта.",
  },
  {
    icon: Lock,
    title: "Защита данных",
    description: "Ключи создаются на вашем устройстве. Мы не храним историю вашей активности.",
  },
  {
    icon: Server,
    title: "Безлимитный трафик",
    description: "Никаких ограничений по объёму данных. Используйте сколько нужно.",
  },
  {
    icon: Eye,
    title: "Политика no-logs",
    description: "Мы не собираем и не храним логи вашей активности.",
  },
];

export function Features() {
  return (
    <section className="px-6 py-20 md:py-32 relative">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            Почему выбирают нас?
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Стабильный канал и удобное подключение без лишних сложностей
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index}
              className="bg-slate-900/50 border-slate-800 backdrop-blur-sm p-8 hover:bg-slate-900/80 transition-all duration-300 hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-500/10"
            >
              <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">
                {feature.title}
              </h3>
              <p className="text-slate-400 leading-relaxed">
                {feature.description}
              </p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
