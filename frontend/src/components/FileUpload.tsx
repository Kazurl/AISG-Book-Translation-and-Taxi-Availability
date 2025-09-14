interface FileUploadProps {
    onFile: (file: File) => void;
}
export default function FileUpload({ onFile }: FileUploadProps) {
    return (
        <input
            type="file"
            accept=".txt"
            onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                    onFile(e.target.files[0]);
                }
            }}
            className="w-full block"
        />
    );
}