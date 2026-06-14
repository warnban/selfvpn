import { Shield, Zap, Globe, Lock, Server, Eye } from "lucide-react";
import { Card } from "./ui/card";

const features = [
  {
    icon: Shield,
    title: "Протокол Amnezia",
    description: "Революционная технология обхода блокировок. Ваш трафик невидим для DPI-систем и провайдеров.",
  },
  {
    icon: Zap,
    title: "Максимальная скорость",
    description: "Серверы с пропускной способностью до 10 Гбит/с. Смотрите 4K видео без задержек и буферизации.",
  },
  {
    icon: Globe,
    title: "50+ стран",
    description: "Подключайтесь к серверам по всему миру. США, Европа, Азия - доступ к любому контенту.",
  },
  {
    icon: Lock,
    title: "AES-256 шифрование",
    description: "Военный уровень защиты данных. Ваша приватность под надежной защитой.",
  },
  {
    icon: Server,
    title: "Безлимитный трафик",
    description: "Никаких ограничений по объему данных. Используйте сколько нужно без дополнительной платы.",
  },
  {
    icon: Eye,
    title: "Политика no-logs",
    description: "Мы не собираем и не храним логи вашей активности. Ваша анонимность гарантирована.",
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
            Передовые технологии защиты и максимальный комфорт использования
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
