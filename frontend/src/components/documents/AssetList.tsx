import React from 'react';
import { FileText, Image as ImageIcon, Trash2, Calendar } from 'lucide-react';
import type { Asset } from '../../types';
import { format } from 'date-fns';

interface AssetListProps {
    assets: Asset[];
    onDelete: (id: string) => void;
}

export const AssetList: React.FC<AssetListProps> = ({ assets, onDelete }) => {
    if (assets.length === 0) {
        return (
            <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-500">
                <FileText className="mb-2 h-8 w-8 opacity-50" />
                <p>No documents uploaded yet</p>
            </div>
        );
    }

    return (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {assets.map((asset) => (
                <div
                    key={asset.id}
                    className="group relative flex flex-col rounded-xl border border-zinc-800 bg-zinc-900 p-4 transition-all hover:border-zinc-700 hover:shadow-lg"
                >
                    <div className="mb-3 flex items-start justify-between">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-800">
                            {asset.asset_type === 'image' ? (
                                <ImageIcon className="h-5 w-5 text-blue-400" />
                            ) : (
                                <FileText className="h-5 w-5 text-orange-400" />
                            )}
                        </div>
                        <button
                            onClick={() => onDelete(asset.id)}
                            className="rounded-lg p-2 text-zinc-500 opacity-0 transition-all hover:bg-red-500/10 hover:text-red-500 group-hover:opacity-100"
                            title="Delete asset"
                        >
                            <Trash2 className="h-4 w-4" />
                        </button>
                    </div>

                    <div className="flex-1">
                        <h4 className="truncate font-medium text-white" title={asset.original_filename}>
                            {asset.original_filename}
                        </h4>
                        <div className="mt-2 flex items-center gap-2 text-xs text-zinc-500">
                            <Calendar className="h-3 w-3" />
                            <span>{format(new Date(asset.created_at), 'MMM d, yyyy')}</span>
                        </div>
                    </div>

                    <div className="mt-3 flex items-center justify-between border-t border-zinc-800 pt-3">
                        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                            {asset.asset_type.toUpperCase()}
                        </span>
                        <a
                            href={asset.cloudinary_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-blue-500 hover:text-blue-400"
                        >
                            View Original
                        </a>
                    </div>
                </div>
            ))}
        </div>
    );
};
