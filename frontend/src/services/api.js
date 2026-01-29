const API_BASE_URL = 'http://127.0.0.1:8000';

export async function uploadMeeting(file, userName, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    onProgress?.('Uploading file...');

    const url = new URL(`${API_BASE_URL}/api/v1/meetings/upload`);
    if (userName) {
      url.searchParams.append('user_name', userName);
    }

    const response = await fetch(url.toString(), {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    onProgress?.('Processing complete!');
    const data = await response.json();
    return data;

  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
}
