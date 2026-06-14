import { Shield, Mail, MessageCircle } from "lucide-react";
import { Button } from "./ui/button";

export function Footer() {
  return (
    <footer className="px-6 py-20 border-t border-slate-800 bg-slate-950/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto">
        {/* CTA Section */}
        <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30 rounded-3xl p-12 mb-16 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Готовы защитить свою приватность?
          </h2>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Присоединяйтесь к тысячам пользователей, которые уже выбрали безопасность и свободу в интернете
          </p>
          <Button 
            size="lg" 
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white text-lg px-8 py-6 shadow-2xl shadow-blue-500/50"
          >
            Начать бесплатный период
          </Button>
          <p className="text-sm text-slate-400 mt-4">
            7 дней бесплатно • Отмена в любой момент • Без привязки карты
          </p>
        </div>
        
        {/* Footer Content */}
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">VPN от Дяди Саши</span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed">
              Надежная защита и полная свобода в интернете с протоколом Amnezia
            </p>
          </div>
          
          {/* Product */}
          <div>
            <h3 className="text-white font-semibold mb-4">Продукт</h3>
            <ul className="space-y-3 text-slate-400 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Возможности</a></li>
              <li><a href="#pricing" className="hover:text-white transition-colors">Тарифы</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Серверы</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Приложения</a></li>
            </ul>
          </div>
          
          {/* Support */}
          <div>
            <h3 className="text-white font-semibold mb-4">Поддержка</h3>
            <ul className="space-y-3 text-slate-400 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Помощь</a></li>
              <li><a href="#" className="hover:text-white transition-colors">FAQ</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Настройка</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Гарантия возврата</a></li>
            </ul>
          </div>
          
          {/* Contact */}
          <div>
            <h3 className="text-white font-semibold mb-4">Контакты</h3>
            <div className="space-y-3">
              <a href="#" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm">
                <Mail className="w-4 h-4" />
                <span>support@vpnuncle.ru</span>
              </a>
              <a href="#" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm">
                <MessageCircle className="w-4 h-4" />
                <span>Telegram: @vpnuncle</span>
              </a>
            </div>
          </div>
        </div>
        
        {/* Bottom */}
        <div className="pt-8 border-t border-slate-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-slate-500 text-sm">
              © 2026 VPN от Дяди Саши. Все права защищены.
            </p>
            <div className="flex gap-6 text-sm text-slate-400">
              <a href="#" className="hover:text-white transition-colors">Политика конфиденциальности</a>
              <a href="#" className="hover:text-white transition-colors">Условия использования</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
