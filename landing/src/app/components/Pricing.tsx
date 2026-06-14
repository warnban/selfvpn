import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Check, Sparkles } from "lucide-react";
import { Badge } from "./ui/badge";

const plans = [
  {
    name: "Месячный",
    price: "390",
    period: "месяц",
    description: "Для тех, кто хочет попробовать",
    features: [
      "Безлимитный трафик",
      "50+ стран",
      "До 5 устройств",
      "Протокол Amnezia",
      "Скорость до 10 Гбит/с",
      "Поддержка 24/7",
    ],
    popular: false,
  },
  {
    name: "Полугодовой",
    price: "290",
    period: "месяц",
    originalPrice: "390",
    description: "Оптимальный выбор",
    features: [
      "Безлимитный трафик",
      "50+ стран",
      "До 10 устройств",
      "Протокол Amnezia",
      "Скорость до 10 Гбит/с",
      "Поддержка 24/7",
      "Приоритетные серверы",
    ],
    popular: true,
  },
  {
    name: "Годовой",
    price: "199",
    period: "месяц",
    originalPrice: "390",
    description: "Максимальная выгода",
    features: [
      "Безлимитный трафик",
      "50+ стран",
      "Безлимитно устройств",
      "Протокол Amnezia",
      "Скорость до 10 Гбит/с",
      "Поддержка 24/7",
      "Приоритетные серверы",
      "Выделенный IP (опция)",
    ],
    popular: false,
    savings: "Экономия 49%",
  },
];

export function Pricing() {
  return (
    <section className="px-6 py-20 md:py-32 relative" id="pricing">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-950/30 to-transparent"></div>
      
      <div className="max-w-7xl mx-auto relative">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            Простые и честные цены
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Выберите подходящий тариф. Все тарифы включают 7 дней бесплатного пробного периода
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <Card 
              key={index}
              className={`relative p-8 ${
                plan.popular 
                  ? 'bg-gradient-to-b from-blue-900/50 to-purple-900/50 border-blue-500 shadow-2xl shadow-blue-500/20 scale-105' 
                  : 'bg-slate-900/50 border-slate-800'
              } backdrop-blur-sm hover:border-blue-500/50 transition-all duration-300`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <Badge className="bg-gradient-to-r from-blue-600 to-purple-600 text-white border-0 px-4 py-1 flex items-center gap-1">
                    <Sparkles className="w-4 h-4" />
                    Популярный
                  </Badge>
                </div>
              )}
              
              {plan.savings && (
                <div className="absolute -top-4 right-4">
                  <Badge className="bg-green-600 text-white border-0 px-3 py-1">
                    {plan.savings}
                  </Badge>
                </div>
              )}
              
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                <p className="text-slate-400 text-sm">{plan.description}</p>
              </div>
              
              <div className="text-center mb-8">
                <div className="flex items-baseline justify-center gap-2">
                  {plan.originalPrice && (
                    <span className="text-2xl text-slate-500 line-through">
                      {plan.originalPrice}₽
                    </span>
                  )}
                  <span className="text-5xl font-bold text-white">
                    {plan.price}₽
                  </span>
                </div>
                <div className="text-slate-400 mt-1">за {plan.period}</div>
              </div>
              
              <div className="space-y-4 mb-8">
                {plan.features.map((feature, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-5 h-5 bg-blue-600/20 rounded-full flex items-center justify-center">
                      <Check className="w-3 h-3 text-blue-400" />
                    </div>
                    <span className="text-slate-300 text-sm">{feature}</span>
                  </div>
                ))}
              </div>
              
              <Button 
                className={`w-full ${
                  plan.popular
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg shadow-blue-500/50'
                    : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700'
                }`}
                size="lg"
              >
                Попробовать бесплатно
              </Button>
              
              <p className="text-center text-xs text-slate-500 mt-4">
                7 дней бесплатно, отмена в любой момент
              </p>
            </Card>
          ))}
        </div>
        
        <div className="text-center mt-12 text-slate-400 text-sm">
          💳 Принимаем карты РФ, криптовалюту, ЮMoney, QIWI
        </div>
      </div>
    </section>
  );
}
