import { useEffect, useState } from 'react';
import api from '../lib/api';
import { FileUploader } from '../components/documents/FileUploader';
import { AssetList } from '../components/documents/AssetList';
import type { Asset } from '../types';
import { Loader2 } from 'lucide-react';

export const DocumentsPage = () => {
    const [assets, setAssets] = useState<Asset[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchAssets = async () => {
        try {
            const response = await api.get('/assets');
            setAssets(response.data.assets);
        } catch (error) {
            console.error('Failed to fetch assets', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this file?')) return;
        try {
            await api.delete(`/assets/${id}`);
            setAssets(assets.filter(a => a.id !== id));
        } catch (error) {
            console.error('Failed to delete asset', error);
            alert('Failed to delete asset');
        }
    };

    useEffect(() => {
        fetchAssets();
    }, []);

    return (
        <div className="flex h-full flex-col overflow-y-auto bg-zinc-950 p-6 sm:p-10">
            <div className="mx-auto w-full max-w-5xl space-y-8">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-bold text-white">Documents</h1>
                    <p className="text-zinc-400">Manage your knowledge base. Uploaded files will be used to answer your questions.</p>
                </div>

                <section>
                    <FileUploader onUploadComplete={fetchAssets} />
                </section>

                <section>
                    <div className="mb-4 flex items-center justify-between">
                        <h2 className="text-xl font-semibold text-white">Your Files ({assets.length})</h2>
                        {loading && <Loader2 className="h-4 w-4 animate-spin text-zinc-500" />}
                    </div>

                    {loading ? (
                        <div className="py-20 text-center text-zinc-500">Loading your assets...</div>
                    ) : (
                        <AssetList assets={assets} onDelete={handleDelete} />
                    )}
                </section>
            </div>
        </div>
    );
};
