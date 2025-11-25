import { useState } from 'react';
import { Book, FileText, Search, FolderOpen, Plus, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useLibraryStore } from '@/store/useLibraryStore';

export const Sidebar = () => {
  const [activeTab, setActiveTab] = useState<'context' | 'notes'>('context');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { papers } = useLibraryStore();

  return (
    <aside 
      className={`
        relative flex h-screen flex-col border-r border-stone-200/60 bg-[#F7F6F3]
        transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-16' : 'w-72'}
      `}
    >
      {/* Collapse Toggle */}
      <button 
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-4 z-20 flex h-6 w-6 items-center justify-center rounded-full border border-stone-200 bg-white text-stone-400 shadow-sm hover:text-stone-600 hover:scale-105 transition-all"
      >
        {isCollapsed ? <PanelLeftOpen size={12} /> : <PanelLeftClose size={12} />}
      </button>

      {/* Header */}
      <div className={`p-4 ${isCollapsed ? 'items-center' : ''} flex flex-col transition-all`}>
        <div className={`flex items-center justify-between ${isCollapsed ? 'justify-center mb-4' : 'mb-4'}`}>
            {!isCollapsed && (
                <div className="flex items-center gap-2 text-stone-700 font-medium tracking-tight">
                    <div className="w-4 h-4 rounded-md bg-gradient-to-br from-orange-400 to-red-500 shadow-sm" />
                    Research OS
                </div>
            )}
            {isCollapsed && (
                 <div className="w-6 h-6 rounded-md bg-gradient-to-br from-orange-400 to-red-500 shadow-sm mb-2" />
            )}
            {!isCollapsed && (
                <button className="p-1 hover:bg-stone-200/60 rounded text-stone-400 hover:text-stone-600 transition-colors">
                    <Plus size={14} />
                </button>
            )}
        </div>
        
        {!isCollapsed && (
            <div className="relative group">
            <Search size={13} className="absolute left-2.5 top-2.5 text-stone-400 group-focus-within:text-stone-600 transition-colors" />
            <input 
                className="w-full rounded-md bg-white border border-stone-200/60 py-1.5 pl-8 pr-3 text-xs text-stone-700 placeholder-stone-400 outline-none focus:border-stone-300 focus:ring-2 focus:ring-stone-100 transition-all shadow-sm"
                placeholder="Search..."
            />
            </div>
        )}
      </div>

      {/* Tabs */}
      <div className={`flex gap-1 px-2 pb-2 border-b border-stone-200/60 ${isCollapsed ? 'flex-col' : ''}`}>
        <SidebarTab 
            label={isCollapsed ? "" : "Context"} 
            icon={<FolderOpen size={16} />} 
            active={activeTab === 'context'} 
            collapsed={isCollapsed}
            onClick={() => setActiveTab('context')}
        />
        <SidebarTab 
            label={isCollapsed ? "" : "Notes"} 
            icon={<FileText size={16} />} 
            active={activeTab === 'notes'} 
            collapsed={isCollapsed}
            onClick={() => setActiveTab('notes')}
        />
      </div>

      {/* List Content */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-hide">
        {activeTab === 'context' ? (
            <>
                {!isCollapsed && <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-stone-400">Papers</div>}
                {papers.map(paper => (
                    <div 
                        key={paper.id}
                        className={`
                            group flex cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-white hover:shadow-sm border border-transparent hover:border-stone-200/60 transition-all
                            ${isCollapsed ? 'justify-center' : ''}
                        `}
                        title={isCollapsed ? paper.title : undefined}
                    >
                        <div className="text-stone-400 group-hover:text-stone-600"><Book size={16} /></div>
                        {!isCollapsed && (
                            <div className="min-w-0">
                                <div className="text-sm font-medium text-stone-700 line-clamp-1">{paper.title}</div>
                                <div className="text-xs text-stone-500">{paper.authors}</div>
                            </div>
                        )}
                    </div>
                ))}
            </>
        ) : (
            <div className="p-4 text-center text-xs text-stone-400">
                {!isCollapsed && "No notes yet."}
            </div>
        )}
      </div>

      {/* Footer */}
      {!isCollapsed && (
          <div className="border-t border-stone-200 p-3 text-xs text-stone-500 flex justify-between bg-stone-100/50">
             <span>Local</span>
             <span>Synced</span>
          </div>
      )}
    </aside>
  );
};

const SidebarTab = ({ label, icon, active, collapsed, onClick }: any) => (
    <button 
        onClick={onClick}
        className={`
            flex items-center justify-center gap-2 rounded-md py-1.5 text-xs font-medium transition-all duration-200
            ${active ? 'bg-white text-stone-800 shadow-[0_1px_2px_rgba(0,0,0,0.04)] border border-stone-200/60' : 'text-stone-500 hover:text-stone-700 hover:bg-stone-200/40'}
            ${collapsed ? 'aspect-square w-full' : 'flex-1'}
        `}
        title={collapsed ? label : undefined}
    >
        {icon}
        {!collapsed && label}
    </button>
);

